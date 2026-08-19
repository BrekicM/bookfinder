import json
import re

from bs4 import BeautifulSoup

from book_finder.domain.models import Availability, Book, Bookstore, Edition
from book_finder.stores.base import CatalogBookstoreClient


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


def _find_product_block(blocks: list[dict]) -> dict | None:
    for block in blocks:
        if block.get("@type") == "Product" and "offers" in block:
            return block
    return None


def _is_book_department(blocks: list[dict]) -> bool:
    # Vulkan's catalog mixes books with merch (board games, mugs, keychains,
    # book lights, etc.) under the same sitemap. The breadcrumb's top-level
    # department (index 2, after "Knjižare Vulkan" and "Proizvodi") is the
    # only reliable signal: books sit under "DOMAĆE KNJIGE" / "ENGLISH BOOKS",
    # while merch sits under "GIFT" / "DRUŠTVENE IGRE" / etc, even when the
    # product name itself contains "knjige" (e.g. a "lampica za knjige").
    for block in blocks:
        if block.get("@type") != "BreadcrumbList":
            continue
        items = block.get("itemListElement", [])
        if len(items) < 3:
            continue
        department = items[2].get("name", "")
        return "knjig" in department.lower() or "book" in department.lower()
    return False


def _author_name(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    link = soup.select_one("a.author-name")
    return link.get_text(strip=True) if link else ""


def _language_from_url(url: str) -> str:
    # Vulkan has no per-product "language" field; foreign-language stock lives
    # under dedicated categories (e.g. "englishbooks-*"). Default: Serbian.
    if re.search(r"/englishbooks", url):
        return "English"
    return "Serbian"


def parse_product_page(html: str) -> Edition | None:
    blocks = _ld_json_blocks(html)
    product_block = _find_product_block(blocks)
    if product_block is None:
        return None
    if not _is_book_department(blocks):
        return None

    title = product_block.get("name", "")
    author = _author_name(html)

    offers = product_block["offers"]
    in_stock = offers.get("availability", "").endswith("InStock")
    availability = Availability.AVAILABLE if in_stock else Availability.NOT_AVAILABLE
    price_rsd = float(offers["price"]) if in_stock and "price" in offers else None
    url = offers.get("url") or product_block.get("url", "")

    return Edition(
        book=Book(title=title, author=author),
        bookstore=Bookstore.VULKAN,
        availability=availability,
        price_rsd=price_rsd,
        language=_language_from_url(url),
        url=url,
    )


class VulkanClient(CatalogBookstoreClient):
    bookstore = Bookstore.VULKAN.value
    sitemap_url = "https://www.knjizare-vulkan.rs/files/sitemap/SRB_rs/product.xml"
    cache_key = "catalog_vulkan"

    def _parse_product_page(self, html: str) -> Edition | None:
        return parse_product_page(html)
