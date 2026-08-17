import httpx

from book_finder.domain.models import Book, Edition
from book_finder.stores.delfi import build_search_url, parse_search_results


def editions_to_search_dicts(editions: list[Edition]) -> list[dict]:
    return books_to_search_dicts([edition.book for edition in editions])


def books_to_search_dicts(books: list[Book]) -> list[dict]:
    return [
        {
            "title": book.title,
            "author_name": [book.author] if book.author else [],
        }
        for book in books
    ]


async def search_delfi_books(query: str, http_client: httpx.AsyncClient) -> list[dict]:
    url = build_search_url(query)
    response = await http_client.get(url, timeout=8.0)
    response.raise_for_status()
    return editions_to_search_dicts(parse_search_results(response.text))
