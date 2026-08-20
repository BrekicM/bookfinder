from pathlib import Path

from book_finder.domain.models import Availability, Bookstore
from book_finder.stores.carobna_knjiga import parse_product_page

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_returns_none_when_no_book_data_present() -> None:
    assert parse_product_page("<html><body>not a book page</body></html>") is None


def test_parses_in_stock_product() -> None:
    edition = parse_product_page(_load("carobna_knjiga_product_in_stock.html"))

    assert edition is not None
    assert edition.bookstore == Bookstore.CAROBNA_KNJIGA
    assert edition.book.title == "Prah"
    assert edition.book.author == "Hju Haui"
    assert edition.availability == Availability.AVAILABLE
    assert edition.price_rsd == 1189.15
    assert edition.language == "Serbian"
    assert edition.script is None
    assert edition.url == "https://carobnaknjiga.rs/prah"


def test_parses_out_of_stock_product() -> None:
    edition = parse_product_page(_load("carobna_knjiga_product_out_of_stock.html"))

    assert edition is not None
    assert edition.book.title == "Hobit"
    assert edition.availability == Availability.NOT_AVAILABLE
    assert edition.price_rsd is None
