import json
from pathlib import Path

import httpx
import pytest

from book_finder.domain.models import Availability, Book, Bookstore
from book_finder.stores.agora import AgoraClient, build_search_url, parse_search_results

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_returns_empty_list_for_zero_results() -> None:
    editions = parse_search_results(_load("agora_search_no_results.json"))
    assert editions == []


def test_parses_real_in_stock_result() -> None:
    editions = parse_search_results(_load("agora_search_results.json"))

    assert len(editions) == 1
    edition = editions[0]
    assert edition.bookstore == Bookstore.AGORA
    assert edition.availability == Availability.AVAILABLE
    assert edition.book.author == "Vladimir Pištalo"
    assert edition.book.title == "LUKE"
    # WooCommerce Store API price is a minor-unit string plus a
    # currency_minor_unit to divide by, same shape as Booka.
    assert edition.price_rsd == 1320.0
    assert edition.language == "Serbian"
    assert edition.format_label == "tvrdi"
    assert edition.script == "Cyrillic"
    assert edition.url == "https://agoraknjige.rs/shop/vladimir-pistalo-luke/"


def test_parses_out_of_stock_result_with_no_price() -> None:
    data = [
        {
            "name": "Neko Drugi: Naslov knjige",
            "permalink": "https://agoraknjige.rs/shop/naslov-knjige/",
            "is_in_stock": False,
            "is_purchasable": True,
            "short_description": "Izdavač: Agora; Godina izdanja: 2020; Jezik: srpski; Pismo: latinica; Povez: mek",
            "prices": {"price": "150000", "currency_minor_unit": 2},
            "categories": [{"name": "Romani"}],
        }
    ]
    editions = parse_search_results(json.dumps(data))

    assert len(editions) == 1
    assert editions[0].availability == Availability.NOT_AVAILABLE
    assert editions[0].price_rsd is None


def test_out_of_stock_result_excluded_from_find_editions_but_kept_by_search_titles() -> None:
    data = [
        {
            "name": "Vladimir Pištalo: LUKE",
            "permalink": "https://agoraknjige.rs/shop/vladimir-pistalo-luke/",
            "is_in_stock": False,
            "is_purchasable": True,
            "short_description": "Izdavač: Agora; Godina izdanja: 2025; Jezik: srpski; Pismo: ćirilica; Povez: tvrdi",
            "prices": {"price": "132000", "currency_minor_unit": 2},
            "categories": [{"name": "Romani"}],
        }
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=json.dumps(data))

    async def run() -> tuple[list, list]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            book = Book(title="LUKE", author="Vladimir Pištalo")
            find_result = await AgoraClient().find_editions(book, http_client)
            search_result = await AgoraClient().search_titles("LUKE", http_client)
            return find_result, search_result

    import asyncio

    find_result, search_result = asyncio.run(run())

    # ADR 0002: a matched-but-out-of-stock Edition must look identical to no
    # match at all in find_editions().
    assert find_result == []
    # search_titles() is pure discovery, never filtered by Availability.
    assert search_result == [Book(title="LUKE", author="Vladimir Pištalo")]


def test_no_colon_title_falls_back_to_empty_author_and_is_not_skipped() -> None:
    data = [
        {
            "name": "Naslov bez dvotačke",
            "permalink": "https://agoraknjige.rs/shop/naslov-bez-dvotacke/",
            "is_in_stock": True,
            "is_purchasable": True,
            "short_description": "Izdavač: Agora; Jezik: srpski; Pismo: latinica; Povez: mek",
            "prices": {"price": "100000", "currency_minor_unit": 2},
            "categories": [{"name": "Romani"}],
        }
    ]
    editions = parse_search_results(json.dumps(data))

    assert len(editions) == 1
    assert editions[0].book.author == ""
    assert editions[0].book.title == "Naslov bez dvotačke"


def test_bundle_suffix_is_stripped_and_shares_identity_with_plain_edition() -> None:
    bundle_data = [
        {
            "name": ("Vladimir Pištalo: TESLA, PORTRET MEĐU MASKAMA + ZVUČNA KNJIGA NA CD-U"),
            "permalink": (
                "https://agoraknjige.rs/shop/"
                "vladimir-pistalo-tesla-portret-medju-maskama-zvucna-knjiga-na-cd-u/"
            ),
            "is_in_stock": True,
            "is_purchasable": True,
            "short_description": "Izdavač: Agora; Godina izdanja: 2022; Jezik: srpski; Pismo: latinica",
            "prices": {"price": "250000", "currency_minor_unit": 2},
            "categories": [{"name": "Romani"}],
        }
    ]
    plain_data = [
        {
            "name": "Vladimir Pištalo: TESLA, PORTRET MEĐU MASKAMA",
            "permalink": "https://agoraknjige.rs/shop/vladimir-pistalo-tesla-portret-medju-maskama/",
            "is_in_stock": True,
            "is_purchasable": True,
            "short_description": "Izdavač: Agora; Godina izdanja: 2022; Jezik: srpski; Pismo: latinica; Povez: tvrd",
            "prices": {"price": "180000", "currency_minor_unit": 2},
            "categories": [{"name": "Romani"}],
        }
    ]

    bundle_editions = parse_search_results(json.dumps(bundle_data))
    plain_editions = parse_search_results(json.dumps(plain_data))

    assert len(bundle_editions) == 1
    bundle = bundle_editions[0]
    assert bundle.book.author == "Vladimir Pištalo"
    assert bundle.book.title == "TESLA, PORTRET MEĐU MASKAMA"
    assert bundle.format_label == "Zvučna knjiga (CD)"

    plain = plain_editions[0]
    assert bundle.book.identity_key() == plain.book.identity_key()


@pytest.mark.parametrize(
    "pismo_value, expected_script",
    [
        ("latinica", "Latin"),
        ("ćirilica", "Cyrillic"),
        ("cirilica", "Cyrillic"),
    ],
)
def test_parses_script_across_separator_styles(pismo_value: str, expected_script: str) -> None:
    semicolon_style = [
        {
            "name": "Neko: Naslov1",
            "permalink": "https://agoraknjige.rs/shop/naslov1/",
            "is_in_stock": True,
            "is_purchasable": True,
            "short_description": (
                f"Izdavač: Agora; Godina izdanja: 2025; Jezik: srpski; "
                f"Pismo: {pismo_value}; Povez: tvrdi"
            ),
            "prices": {"price": "100000", "currency_minor_unit": 2},
            "categories": [{"name": "Romani"}],
        }
    ]
    spaced_style = [
        {
            "name": "Neko: Naslov2",
            "permalink": "https://agoraknjige.rs/shop/naslov2/",
            "is_in_stock": True,
            "is_purchasable": True,
            "short_description": (
                "Žanr knjige: roman Izdavač: Agora Godina izdanja: 2011 "
                "ISBN broj: 978-86-6053-054-9 Broj strana: 424 "
                f"Pismo: {pismo_value} Jezik: srpski Povez: tvrd povez Format: 24×16"
            ),
            "prices": {"price": "100000", "currency_minor_unit": 2},
            "categories": [{"name": "Romani"}],
        }
    ]

    for data in (semicolon_style, spaced_style):
        editions = parse_search_results(json.dumps(data))
        assert len(editions) == 1
        assert editions[0].script == expected_script


def test_povez_format_label_for_non_bundle_listings() -> None:
    semicolon_style = [
        {
            "name": "Neko: Naslov1",
            "permalink": "https://agoraknjige.rs/shop/naslov1/",
            "is_in_stock": True,
            "is_purchasable": True,
            "short_description": (
                "Izdavač: Agora; Godina izdanja: 2025; Jezik: srpski; Pismo: ćirilica; Povez: tvrdi"
            ),
            "prices": {"price": "100000", "currency_minor_unit": 2},
            "categories": [{"name": "Romani"}],
        }
    ]
    spaced_style = [
        {
            "name": "Neko: Naslov2",
            "permalink": "https://agoraknjige.rs/shop/naslov2/",
            "is_in_stock": True,
            "is_purchasable": True,
            "short_description": (
                "Žanr knjige: roman Izdavač: Agora Godina izdanja: 2011 "
                "ISBN broj: 978-86-6053-054-9 Broj strana: 424 "
                "Pismo: latinica Jezik: srpski Povez: tvrd povez Format: 24×16"
            ),
            "prices": {"price": "100000", "currency_minor_unit": 2},
            "categories": [{"name": "Romani"}],
        }
    ]

    semicolon_editions = parse_search_results(json.dumps(semicolon_style))
    spaced_editions = parse_search_results(json.dumps(spaced_style))

    assert semicolon_editions[0].format_label == "tvrdi"
    assert spaced_editions[0].format_label == "tvrd povez"


def test_missing_or_unrecognized_jezik_defaults_language_to_serbian() -> None:
    no_jezik = [
        {
            "name": "Neko: Naslov bez jezika",
            "permalink": "https://agoraknjige.rs/shop/naslov-bez-jezika/",
            "is_in_stock": True,
            "is_purchasable": True,
            "short_description": "Izdavač: Agora; Godina izdanja: 2025; Pismo: latinica; Povez: mek",
            "prices": {"price": "100000", "currency_minor_unit": 2},
            "categories": [{"name": "Romani"}],
        }
    ]
    editions = parse_search_results(json.dumps(no_jezik))
    assert editions[0].language == "Serbian"


def test_skips_results_missing_required_fields() -> None:
    data = [{"permalink": "https://agoraknjige.rs/shop/x/"}]
    assert parse_search_results(json.dumps(data)) == []

    data_no_permalink = [{"name": "Neko: Naslov"}]
    assert parse_search_results(json.dumps(data_no_permalink)) == []


def test_build_search_url_encodes_spaces() -> None:
    url = build_search_url("Luke Pistalo")
    assert url.endswith("Luke%20Pistalo")


def test_build_search_url_encodes_slashes_in_the_query() -> None:
    url = build_search_url("A / B")
    assert "%2F" in url
