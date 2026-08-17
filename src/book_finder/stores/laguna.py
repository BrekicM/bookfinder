import json

from bs4 import BeautifulSoup

from book_finder.domain.models import Availability, Book, Bookstore, Edition
from book_finder.stores.base import BookstoreClient

_LANGUAGE_NAMES = {
    "sr": "Serbian",
    "en": "English",
    "ru": "Russian",
}


def _ld_json_blocks(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    blocks = []
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            blocks.append(json.loads(script.string))
        except json.JSONDecodeError:
            continue
    return blocks


def _find_book_block(blocks: list[dict]) -> dict | None:
    for block in blocks:
        types = block.get("@type")
        if types == "Book" or (isinstance(types, list) and "Book" in types):
            return block
    return None


def _find_breadcrumb_title(blocks: list[dict]) -> str | None:
    for block in blocks:
        if block.get("@type") != "BreadcrumbList":
            continue
        items = block.get("itemListElement", [])
        if items:
            return items[-1].get("name")
    return None


def parse_product_page(html: str) -> Edition | None:
    blocks = _ld_json_blocks(html)
    book_block = _find_book_block(blocks)
    if book_block is None:
        return None

    title = _find_breadcrumb_title(blocks) or book_block.get("name", "")
    authors = book_block.get("author") or []
    author = authors[0].get("name", "") if authors else ""

    lang_code = book_block.get("inLanguage", "")
    language = _LANGUAGE_NAMES.get(lang_code, lang_code)

    offers = book_block.get("offers", {})
    in_stock = offers.get("availability", "").endswith("InStock")
    availability = Availability.AVAILABLE if in_stock else Availability.NOT_AVAILABLE
    price_rsd = float(offers["price"]) if in_stock and "price" in offers else None
    url = offers.get("url") or book_block.get("url", "")

    return Edition(
        book=Book(title=title, author=author),
        bookstore=Bookstore.LAGUNA,
        availability=availability,
        price_rsd=price_rsd,
        language=language,
        url=url,
    )


class LagunaClient(BookstoreClient):
    bookstore = Bookstore.LAGUNA.value
    sitemap_url = "https://laguna.rs/sitemap/products/1/"
    cache_key = "catalog_laguna"

    def _is_book_url(self, url: str) -> bool:
        return "/proizvodi/knjige/" in url

    def _parse_product_page(self, html: str) -> Edition | None:
        return parse_product_page(html)
