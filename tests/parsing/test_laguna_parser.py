from pathlib import Path

from book_finder.domain.models import Availability, Bookstore
from book_finder.stores.laguna import parse_product_page

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_returns_none_when_no_book_data_present() -> None:
    assert parse_product_page("<html><body>not a book page</body></html>") is None


def test_parses_in_stock_product() -> None:
    edition = parse_product_page(_load("laguna_product_in_stock.html"))

    assert edition is not None
    assert edition.bookstore == Bookstore.LAGUNA
    assert edition.availability == Availability.AVAILABLE
    assert edition.book.title == "Kosingas 2: Bezdanj"
    assert edition.book.author == "Aleksandar Tešić"
    assert edition.price_rsd == 1899.0
    assert edition.language == "Serbian"
    assert edition.url == "https://laguna.rs/proizvodi/knjige/kosingas-2-bezdanj/"


def test_parses_out_of_stock_product_with_no_price() -> None:
    edition = parse_product_page(_load("laguna_product_out_of_stock.html"))

    assert edition is not None
    assert edition.availability == Availability.NOT_AVAILABLE
    assert edition.price_rsd is None
    # title comes from the breadcrumb, not the noisy marketing "name" field
    assert edition.book.title == "Urgum Sekiraš"
    assert edition.book.author == "Kjartan Poskit"
