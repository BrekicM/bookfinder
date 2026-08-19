import asyncio
import json
from urllib.parse import quote

import httpx

from book_finder.config import settings
from book_finder.domain.models import Availability, Book, Bookstore, Edition
from book_finder.stores.base import BookstoreClient, matches_book, matches_query
from book_finder.stores.slugify import slugify

SEARCH_URL = "https://delfi.rs/api/pc-frontend-api/search/quick-search-products/{category}/{query}"

# The unscoped "Sve kategorije" (all categories) search is capped at a
# handful of results ranked across Delfi's whole catalog, so for a
# franchise with heavily-stocked merchandise (mugs, stickers, plushies...)
# actual books can be crowded out entirely. Scoping to these two book
# categories (found by probing the endpoint's own category segment)
# returns real books instead. See ADR 0004's "Update" section.
BOOK_CATEGORIES = ("Knjiga", "Strana knjiga")


def build_search_url(query: str, category: str = "Sve kategorije") -> str:
    # quote(..., safe="") also encodes "/", which appears in real titles
    # (omnibus editions like "A / B / C") and would otherwise be read as
    # extra path segments by Delfi's path-based search endpoint, 404ing.
    return SEARCH_URL.format(category=quote(category, safe=""), query=quote(query, safe=""))


def parse_search_results(raw_json: str) -> list[Edition]:
    data = json.loads(raw_json)
    results = data.get("data", {}).get("results", [])

    editions = []
    for item in results:
        product_id = item.get("oldProductId")
        title = item.get("title")
        if product_id is None or not title:
            continue

        authors = item.get("authors") or []
        author = authors[0].get("authorName", "") if authors else ""

        is_available = bool(item.get("isAvailable", False))
        price = item.get("priceList", {}).get("regularDiscountPrice") if is_available else None

        editions.append(
            Edition(
                book=Book(title=title, author=author),
                bookstore=Bookstore.DELFI,
                availability=Availability.AVAILABLE if is_available else Availability.NOT_AVAILABLE,
                price_rsd=float(price) if price is not None else None,
                # No language field is exposed by this API (mirrors Vulkan);
                # Delfi is Serbia's largest domestic retailer, so default fits.
                language="Serbian",
                format_label=item.get("cover"),
                url=f"https://delfi.rs/knjige/{product_id}-{slugify(title)}.html",
            )
        )
    return editions


async def fetch_book_editions(query: str, http_client: httpx.AsyncClient) -> list[Edition]:
    """Search across BOOK_CATEGORIES and merge, deduping by product URL.

    A single "Sve kategorije" (all categories) search is capped and ranked
    across Delfi's whole catalog, so for a heavily-merchandised franchise
    (mugs, stickers, plushies...) real books can be crowded out of the
    results entirely — searching the book categories directly avoids that.
    """
    responses = await asyncio.gather(
        *(
            http_client.get(
                build_search_url(query, category=category),
                timeout=settings.store_request_timeout_seconds,
            )
            for category in BOOK_CATEGORIES
        )
    )

    editions: list[Edition] = []
    seen_urls: set[str] = set()
    for response in responses:
        response.raise_for_status()
        for edition in parse_search_results(response.text):
            if edition.url not in seen_urls:
                seen_urls.add(edition.url)
                editions.append(edition)

    return editions


async def search_books(query: str, http_client: httpx.AsyncClient) -> list[Edition]:
    """Free-text search discovery, filtered to titles relevant to the query.

    Delfi's quick-search endpoint does its own fuzzy/ranked matching and can
    return hits with little to no textual overlap with the query. Unlike
    find_editions(), this doesn't gate on Availability — a book should stay
    discoverable via search even when out of stock.
    """
    candidates = await fetch_book_editions(query, http_client)
    return [
        edition
        for edition in candidates
        if matches_query(candidate_title=edition.book.title, query=query)
    ]


class DelfiClient(BookstoreClient):
    """Unlike Laguna/Vulkan, Delfi has a real internal search API — found by
    capturing the live site's own network requests (its search box calls
    pc-frontend-api/search/quick-search-products), not by guessing endpoint
    names. No headless browser or catalog cache needed; see ADR 0004, which
    supersedes ADR 0003's original (incorrect) assumption.
    """

    bookstore = Bookstore.DELFI.value

    async def search_titles(self, query: str, http_client: httpx.AsyncClient) -> list[Book]:
        """Free-text search discovery via Delfi's own search API.

        Unlike find_editions(), results are not filtered by Availability — a
        Book stays discoverable via search even when out of stock (ADR 0002).
        """
        editions = await search_books(query, http_client)
        return [edition.book for edition in editions]

    async def find_editions(self, book: Book, http_client: httpx.AsyncClient) -> list[Edition]:
        candidates = await fetch_book_editions(book.title, http_client)
        return [
            edition
            for edition in candidates
            if edition.availability == Availability.AVAILABLE
            and matches_book(
                candidate_title=edition.book.title,
                candidate_author=edition.book.author,
                book=book,
            )
        ]
