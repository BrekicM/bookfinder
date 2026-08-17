import json

import httpx

from book_finder.domain.models import Availability, Book, Bookstore, Edition
from book_finder.stores.base import BookstoreClient, matches_book
from book_finder.stores.slugify import slugify

SEARCH_URL = "https://delfi.rs/api/pc-frontend-api/search/quick-search-products/Sve kategorije/{query}"


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


class DelfiClient(BookstoreClient):
    """Unlike Laguna/Vulkan, Delfi has a real internal search API — found by
    capturing the live site's own network requests (its search box calls
    pc-frontend-api/search/quick-search-products), not by guessing endpoint
    names. No headless browser or catalog cache needed; see ADR 0004, which
    supersedes ADR 0003's original (incorrect) assumption.
    """

    bookstore = Bookstore.DELFI.value

    def _parse_product_page(self, html: str) -> Edition | None:
        raise NotImplementedError("DelfiClient overrides find_editions() directly")

    async def find_editions(self, book: Book, http_client: httpx.AsyncClient) -> list[Edition]:
        url = SEARCH_URL.format(query=book.title)
        response = await http_client.get(url, timeout=8.0)
        response.raise_for_status()

        candidates = parse_search_results(response.text)
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
