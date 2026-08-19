import html
import json
from urllib.parse import quote

import httpx

from book_finder.config import settings
from book_finder.domain.models import Availability, Book, Bookstore, Edition
from book_finder.stores.base import BookstoreClient, matches_book, url_slug

SEARCH_URL = "https://booka.rs/wp-json/wc/store/v1/products?search={query}"
PRODUCT_URL = "https://booka.rs/wp-json/wp/v2/product?slug={slug}"
PISAC_URL = "https://booka.rs/wp-json/wp/v2/pisac/{term_id}"

# Booka's search API mixes books with merch (tote bags, etc.) sharing the same
# catalog. Book product pages live under /knjige/; everything else is not a
# Book/Edition for this app's purposes.
BOOK_PATH_SEGMENT = "/knjige/"

_SCRIPT_LABELS = {"latinica": "Latin", "ćirilica": "Cyrillic", "cirilica": "Cyrillic"}


def build_search_url(query: str) -> str:
    # quote(..., safe="") also encodes "/", matching Delfi's handling of
    # titles containing slashes (omnibus editions).
    return SEARCH_URL.format(query=quote(query, safe=""))


def _attribute_value(item: dict, name: str) -> str | None:
    for attribute in item.get("attributes", []):
        if attribute.get("name") == name:
            terms = attribute.get("terms") or []
            if terms:
                return terms[0].get("name")
    return None


def _script_label(raw: str | None) -> str | None:
    if raw is None:
        return None
    return _SCRIPT_LABELS.get(raw.strip().lower(), raw)


def _price_rsd(prices: dict) -> float | None:
    raw_price = prices.get("price")
    minor_unit = prices.get("currency_minor_unit")
    if raw_price in (None, "") or minor_unit is None:
        return None
    return float(raw_price) / (10**minor_unit)


def parse_search_item(item: dict) -> Edition | None:
    permalink = item.get("permalink")
    name = item.get("name")
    if not permalink or not name or BOOK_PATH_SEGMENT not in permalink:
        return None

    is_available = bool(item.get("is_in_stock", False))
    price = _price_rsd(item.get("prices", {})) if is_available else None

    return Edition(
        book=Book(title=html.unescape(name), author=""),
        bookstore=Bookstore.BOOKA,
        availability=Availability.AVAILABLE if is_available else Availability.NOT_AVAILABLE,
        price_rsd=price,
        # Booka's Store API doesn't expose the edition's language directly,
        # but it's a domestic Serbian retailer selling translated/domestic
        # literature (mirrors Delfi/Vulkan's same default).
        language="Serbian",
        format_label=_attribute_value(item, "Povez"),
        script=_script_label(_attribute_value(item, "Pismo")),
        url=permalink,
    )


def parse_search_results(raw_json: str) -> list[Edition]:
    data = json.loads(raw_json)
    editions = []
    for item in data:
        edition = parse_search_item(item)
        if edition is not None:
            editions.append(edition)
    return editions


async def fetch_search_results(query: str, http_client: httpx.AsyncClient) -> list[Edition]:
    response = await http_client.get(
        build_search_url(query), timeout=settings.store_request_timeout_seconds
    )
    response.raise_for_status()
    return parse_search_results(response.text)


async def search_books(query: str, http_client: httpx.AsyncClient) -> list[Edition]:
    """Free-text search discovery, filtered to the query and author-resolved.

    Booka's search endpoint does its own fuzzy matching and returns hits
    with little to no textual overlap with the query, and never includes
    author inline (see parse_search_item). Unlike find_editions(), this
    doesn't gate on Availability — a book should stay discoverable via
    search even when out of stock (mirrors BookstoreClient.search_titles).
    """
    candidates = await fetch_search_results(query, http_client)
    query_book = Book(title=query, author="")

    matched = [
        edition
        for edition in candidates
        if matches_book(candidate_title=edition.book.title, candidate_author="", book=query_book)
    ]

    editions = []
    for edition in matched:
        author = await resolve_author(url_slug(edition.url), http_client)
        editions.append(
            edition.model_copy(update={"book": Book(title=edition.book.title, author=author)})
        )
    return editions


async def resolve_author(slug: str, http_client: httpx.AsyncClient) -> str:
    """Two-step author lookup: product -> pisac term id -> pisac name.

    Returns "" on any failure (network error, no product, no pisac terms) —
    callers must treat that as "author unknown", never as "any author
    matches" (that fallback is only valid for stores with no author data at
    all, e.g. Delfi/Vulkan; Booka does have author data, so a failed lookup
    here is a real gap, not the store's design).
    """
    try:
        response = await http_client.get(
            PRODUCT_URL.format(slug=slug),
            timeout=settings.store_request_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return ""

    products = response.json()
    if not products:
        return ""

    pisac_ids = products[0].get("pisac") or []
    if not pisac_ids:
        return ""

    try:
        author_response = await http_client.get(
            PISAC_URL.format(term_id=pisac_ids[0]),
            timeout=settings.store_request_timeout_seconds,
        )
        author_response.raise_for_status()
    except httpx.HTTPError:
        return ""

    name = author_response.json().get("name", "")
    return html.unescape(name) if name else ""


class BookaClient(BookstoreClient):
    """Booka exposes a documented WooCommerce Store API search endpoint, used
    directly (like DelfiClient), rather than the sitemap-and-shortlist base.
    See ADR 0009. Author isn't inline in the search response, so it's
    resolved in a second (and third) call, but only for candidates that
    already match on title — resolving every raw search hit's author would
    be wasteful and unnecessary.
    """

    bookstore = Bookstore.BOOKA.value

    async def search_titles(self, query: str, http_client: httpx.AsyncClient) -> list[Book]:
        """Free-text search discovery via Booka's own search API.

        Unlike find_editions(), results are not filtered by Availability — a
        Book stays discoverable via search even when out of stock (ADR 0002).
        Author is resolved per matching candidate, as search_books() does.
        """
        editions = await search_books(query, http_client)
        return [edition.book for edition in editions]

    async def find_editions(self, book: Book, http_client: httpx.AsyncClient) -> list[Edition]:
        candidates = await fetch_search_results(book.title, http_client)

        # Cheap title-only shortlist first. candidate_author="" here means
        # "author not checked yet", not "any author matches" for the final
        # result — that distinction is enforced below, before anything is
        # actually included.
        shortlisted = [
            edition
            for edition in candidates
            if edition.availability == Availability.AVAILABLE
            and matches_book(candidate_title=edition.book.title, candidate_author="", book=book)
        ]

        editions = []
        for edition in shortlisted:
            author = await resolve_author(url_slug(edition.url), http_client)
            if not author and book.author.strip():
                # Author lookup genuinely failed/unknown and the query cares
                # about author — do not let matches_book's "no author data"
                # fallback silently pass this through.
                continue
            if matches_book(candidate_title=edition.book.title, candidate_author=author, book=book):
                editions.append(
                    edition.model_copy(
                        update={"book": Book(title=edition.book.title, author=author)}
                    )
                )

        return editions
