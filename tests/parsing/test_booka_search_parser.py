import json
from pathlib import Path

from book_finder.domain.models import Availability, Bookstore
from book_finder.stores.booka import build_search_url, parse_search_results

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_returns_empty_list_for_zero_results() -> None:
    editions = parse_search_results(_load("booka_search_no_results.json"))
    assert editions == []


def test_parses_real_in_stock_result() -> None:
    editions = parse_search_results(_load("booka_search_results.json"))

    assert len(editions) == 1
    edition = editions[0]
    assert edition.bookstore == Bookstore.BOOKA
    assert edition.availability == Availability.AVAILABLE
    assert edition.book.title == "Brana na Atlantiku"
    assert edition.book.author == ""
    # WooCommerce Store API price is a minor-unit string ("89100") plus a
    # currency_minor_unit (2) to divide by — confirmed via a real request,
    # not the plain-decimal-string shape originally assumed.
    assert edition.price_rsd == 891.0
    assert edition.language == "Serbian"
    assert edition.format_label == "mek"
    assert edition.script == "Latin"
    assert (
        edition.url
        == "https://booka.rs/knjige/savremena-knjizevnost/brana-na-atlantiku/"
    )


def test_parses_out_of_stock_result_with_no_price() -> None:
    # Constructed from the real API's confirmed schema (is_in_stock/prices/
    # permalink/attributes fields, verified via a live request against a
    # genuinely out-of-stock title), not fabricated from scratch.
    data = [
        {
            "name": "Some Out Of Stock Book",
            "permalink": "https://booka.rs/knjige/some-genre/some-out-of-stock-book/",
            "is_in_stock": False,
            "is_purchasable": True,
            "prices": {"price": "150000", "currency_minor_unit": 2},
            "attributes": [
                {"name": "Povez", "terms": [{"name": "tvrd"}]},
                {"name": "Pismo", "terms": [{"name": "latinica"}]},
            ],
        }
    ]
    editions = parse_search_results(json.dumps(data))

    assert len(editions) == 1
    assert editions[0].availability == Availability.NOT_AVAILABLE
    assert editions[0].price_rsd is None
    assert editions[0].format_label == "tvrd"


def test_filters_out_non_book_products() -> None:
    # Booka's Store API search returns merch (tote bags etc.) alongside books
    # when a query matches both; only /knjige/ permalinks are books.
    editions = parse_search_results(_load("booka_search_mixed_with_gift_item.json"))

    titles = {edition.book.title for edition in editions}
    assert titles == {"Brana na Atlantiku", "Forsiranje romana-reke"}
    assert all("/knjige/" in edition.url for edition in editions)


def test_skips_results_missing_required_fields() -> None:
    data = [{"permalink": "https://booka.rs/knjige/x/"}]
    assert parse_search_results(json.dumps(data)) == []


def test_build_search_url_encodes_spaces() -> None:
    url = build_search_url("Na Rubu Pameti")
    assert url.endswith("Na%20Rubu%20Pameti")


def test_build_search_url_encodes_slashes_in_the_query() -> None:
    url = build_search_url("A / B")
    assert "%2F" in url
