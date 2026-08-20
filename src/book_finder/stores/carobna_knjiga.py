from bs4 import BeautifulSoup

from book_finder.config import settings
from book_finder.domain.models import Availability, Book, Bookstore, Edition
from book_finder.stores.base import CatalogBookstoreClient

# Čarobna knjiga has no books-only catalog listing or sitemap signal (see ADR
# 0010): /knjige is a landing page, not a paginated grid, and the sitemap and
# the "chronological" listing both mix books with comics/manga on identical
# product-page markup. Genre category pages, however, are cleanly single-
# typed. There's no structural marker distinguishing a book-genre page from a
# comic-genre page (no heading, wrapping container, or reliable slug-suffix
# pattern — comic genres like "betmen", "dedpul", "dc-mejnstrim" carry no
# "-strip"/"u-stripu" suffix at all), so this list was built by fetching every
# genre listed on /zanrovi and checking its own products by hand. Adding a new
# book genre on the site requires updating this list by hand too.
BOOK_GENRE_SLUGS = [
    "kompleti-knjiga",
    "ljubavni-romani",
    "domaca-knjizevnost",
    "dečja-književnost",
    "fantastika",
    "horor",
    "istorijski-romani",
    "zanimljivi-naslovi",
    "popularna-beletristika",
    "savremena-knjizevnost",
    "tinejdzerska-knjizevnost",
    "triler",
    "samousavršavanje-popularna-psihologija",
]


def _author_name(soup: BeautifulSoup) -> str:
    for p in soup.select("p.no-margin"):
        if p.get_text().strip().startswith("Autor:"):
            link = p.select_one('a[href*="/autori/"]')
            if link is not None:
                return link.get_text(strip=True)
    return ""


def _availability(soup: BeautifulSoup) -> Availability:
    badge = soup.select_one("span.badge")
    if badge is not None and badge.get_text(strip=True) == "Dostupno":
        return Availability.AVAILABLE
    return Availability.NOT_AVAILABLE


def _price_rsd(soup: BeautifulSoup) -> float | None:
    for block in soup.select("div.product-price"):
        if "Vaša cena" not in block.get_text():
            continue
        span = block.select_one("span")
        if span is None:
            continue
        text = span.get_text(strip=True)
        text = text.replace(" RSD", "").replace(".", "").replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _url(soup: BeautifulSoup) -> str:
    meta = soup.select_one('meta[property="og:url"]')
    return meta["content"] if meta is not None else ""


def parse_product_page(html: str) -> Edition | None:
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.select_one("h1.heading-2")
    if title_tag is None:
        return None

    title = title_tag.get_text(strip=True)
    author = _author_name(soup)
    availability = _availability(soup)
    price_rsd = _price_rsd(soup) if availability == Availability.AVAILABLE else None

    return Edition(
        book=Book(title=title, author=author),
        bookstore=Bookstore.CAROBNA_KNJIGA,
        availability=availability,
        price_rsd=price_rsd,
        language="Serbian",
        script=None,
        url=_url(soup),
    )


def _next_page_disabled(soup: BeautifulSoup) -> bool:
    for li in soup.select("ul.pagination li"):
        link = li.find("a")
        if link is not None and link.get_text(strip=True) == "Sledeća":
            classes = li.get("class") or []
            return "disabled" in classes
    return True


class CarobnaKnjigaClient(CatalogBookstoreClient):
    bookstore = Bookstore.CAROBNA_KNJIGA.value
    cache_key = "catalog_carobna_knjiga"

    def _parse_product_page(self, html: str) -> Edition | None:
        return parse_product_page(html)

    async def _fetch_catalog_urls(self, http_client) -> list[str]:
        urls: list[str] = []
        for slug in BOOK_GENRE_SLUGS:
            page = 1
            while True:
                response = await http_client.get(
                    f"https://carobnaknjiga.rs/{slug}/{page}",
                    timeout=settings.store_request_timeout_seconds,
                )
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")
                for a in soup.select("div.product-image a[href]"):
                    href = a["href"]
                    if href not in urls:
                        urls.append(href)

                if _next_page_disabled(soup):
                    break
                page += 1

        return urls
