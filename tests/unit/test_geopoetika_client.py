from pathlib import Path

from book_finder.domain.models import Availability, Bookstore
from book_finder.stores.geopoetika import GeopoetikaClient

FIXTURES = Path(__file__).parent.parent / "parsing" / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_bookstore_is_geopoetika() -> None:
    assert GeopoetikaClient.bookstore == Bookstore.GEOPOETIKA.value


def test_sitemap_url_points_at_geopoetika_sitemap() -> None:
    assert GeopoetikaClient.sitemap_url == "https://geopoetika.com/sitemap.xml"


def test_is_book_url_includes_product_pages() -> None:
    client = GeopoetikaClient()
    assert client._is_book_url("https://geopoetika.com/o-knjizi/3331/nasi-stranci")


def test_is_book_url_excludes_static_pages() -> None:
    client = GeopoetikaClient()
    static_pages = [
        "https://geopoetika.com/",
        "https://geopoetika.com/books",
        "https://geopoetika.com/authors",
        "https://geopoetika.com/articles",
        "https://geopoetika.com/page/o-nama",
        "https://geopoetika.com/page/kontakt",
    ]
    for url in static_pages:
        assert not client._is_book_url(url)


def test_parse_product_page_delegates_to_the_module_level_parser() -> None:
    client = GeopoetikaClient()
    edition = client._parse_product_page(_load("geopoetika_product_in_stock.html"))

    assert edition is not None
    assert edition.bookstore == Bookstore.GEOPOETIKA
    assert edition.book.title == "Naši stranci"
    assert edition.availability == Availability.AVAILABLE
