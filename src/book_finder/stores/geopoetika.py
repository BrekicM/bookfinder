import re

from bs4 import BeautifulSoup

from book_finder.domain.models import Availability, Book, Bookstore, Edition
from book_finder.stores.base import CatalogBookstoreClient


def _author(soup: BeautifulSoup) -> str:
    tag = soup.select_one("p.author")
    return tag.get_text(strip=True) if tag is not None else ""


def _url(soup: BeautifulSoup) -> str:
    meta = soup.select_one('meta[property="og:url"]')
    return meta["content"] if meta is not None else ""


def _availability_and_price(soup: BeautifulSoup) -> tuple[Availability, float | None]:
    price_tag = soup.select_one("p.price")
    if price_tag is None:
        return Availability.NOT_AVAILABLE, None

    if "Rasprodato" in price_tag.get_text():
        return Availability.NOT_AVAILABLE, None

    # The struck-through list price lives in a nested <del>; drop it so only
    # the discounted, buyer-facing price remains (see ADR 0011).
    del_tag = price_tag.find("del")
    if del_tag is not None:
        del_tag.extract()

    match = re.search(r"([\d.,]+)\s*din", price_tag.get_text())
    if match is None:
        return Availability.AVAILABLE, None

    price_text = match.group(1).replace(".", "").replace(",", ".")
    try:
        return Availability.AVAILABLE, float(price_text)
    except ValueError:
        return Availability.AVAILABLE, None


def parse_product_page(html: str) -> Edition | None:
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.select_one("h1.title")
    if title_tag is None:
        return None

    availability, price_rsd = _availability_and_price(soup)

    return Edition(
        book=Book(title=title_tag.get_text(strip=True), author=_author(soup)),
        bookstore=Bookstore.GEOPOETIKA,
        availability=availability,
        price_rsd=price_rsd,
        language="Serbian",
        script=None,
        url=_url(soup),
    )


class GeopoetikaClient(CatalogBookstoreClient):
    bookstore = Bookstore.GEOPOETIKA.value
    cache_key = "catalog_geopoetika"
    sitemap_url = "https://geopoetika.com/sitemap.xml"

    def _is_book_url(self, url: str) -> bool:
        return "/o-knjizi/" in url

    def _parse_product_page(self, html: str) -> Edition | None:
        return parse_product_page(html)
