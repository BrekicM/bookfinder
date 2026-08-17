import json
from pathlib import Path

from book_finder.domain.models import Availability, Bookstore
from book_finder.stores.delfi import parse_search_results

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_returns_empty_list_for_zero_results() -> None:
    editions = parse_search_results(_load("delfi_search_no_results.json"))
    assert editions == []


def test_parses_real_in_stock_result() -> None:
    editions = parse_search_results(_load("delfi_search_results.json"))

    assert len(editions) == 1
    edition = editions[0]
    assert edition.bookstore == Bookstore.DELFI
    assert edition.availability == Availability.AVAILABLE
    assert edition.book.title == "Na meni je"
    assert edition.book.author == "Sara Kuburić"
    assert edition.price_rsd == 2499.0
    assert edition.language == "Serbian"
    assert edition.format_label == "Mek"
    assert edition.url == "https://delfi.rs/knjige/205745-na-meni-je.html"


def test_parses_out_of_stock_result_with_no_price() -> None:
    # Constructed from the real API's confirmed schema (isAvailable/priceList/
    # oldProductId fields), not a captured response — no out-of-stock item
    # was found in the sample searches used during development.
    data = {
        "data": {
            "results": [
                {
                    "oldProductId": 999999,
                    "title": "Some Out Of Stock Book",
                    "authors": [{"authorName": "Some Author"}],
                    "isAvailable": False,
                    "priceList": {"regularDiscountPrice": 1500},
                    "cover": "Tvrd",
                }
            ]
        }
    }
    editions = parse_search_results(json.dumps(data))

    assert len(editions) == 1
    assert editions[0].availability == Availability.NOT_AVAILABLE
    assert editions[0].price_rsd is None
    assert editions[0].format_label == "Tvrd"


def test_skips_results_missing_required_fields() -> None:
    data = {"data": {"results": [{"title": "No ID Here"}]}}
    assert parse_search_results(json.dumps(data)) == []
