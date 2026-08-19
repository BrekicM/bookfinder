import httpx

from book_finder.domain.models import Book, Edition
from book_finder.stores.booka import search_books as search_booka_editions
from book_finder.stores.delfi import search_books as search_delfi_editions


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
    editions = await search_delfi_editions(query, http_client)
    return editions_to_search_dicts(editions)


async def search_booka_books(query: str, http_client: httpx.AsyncClient) -> list[dict]:
    editions = await search_booka_editions(query, http_client)
    return editions_to_search_dicts(editions)
