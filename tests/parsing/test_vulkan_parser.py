from pathlib import Path

from book_finder.domain.models import Availability, Bookstore
from book_finder.stores.vulkan import parse_product_page

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_returns_none_when_no_book_data_present() -> None:
    assert parse_product_page("<html><body>not a book page</body></html>") is None


def test_parses_out_of_stock_serbian_product() -> None:
    edition = parse_product_page(_load("vulkan_product_out_of_stock.html"))

    assert edition is not None
    assert edition.bookstore == Bookstore.VULKAN
    assert edition.availability == Availability.NOT_AVAILABLE
    assert edition.price_rsd is None
    assert edition.book.title == "STAZA PAUKOVIH GNEZDA"
    assert edition.book.author == "Italo Kalvino"
    assert edition.language == "Serbian"
    assert edition.url == "https://www.knjizare-vulkan.rs/roman/311296-staza-paukovih-gnezda"


def test_parses_in_stock_english_product() -> None:
    edition = parse_product_page(_load("vulkan_product_in_stock_english.html"))

    assert edition is not None
    assert edition.availability == Availability.AVAILABLE
    assert edition.price_rsd == 3740.0
    assert edition.book.author == "Adam Nayman"
    assert edition.language == "English"


def test_rejects_non_book_merchandise() -> None:
    edition = parse_product_page(_load("vulkan_product_non_book_board_game.html"))

    assert edition is None
