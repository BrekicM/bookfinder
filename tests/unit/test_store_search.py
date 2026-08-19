import json

import httpx
import pytest

from book_finder.domain.models import Availability, Book, Bookstore, Edition
from book_finder.search.store_search import (
    books_to_search_dicts,
    editions_to_search_dicts,
    search_booka_books,
)


def test_empty_list_returns_empty() -> None:
    assert editions_to_search_dicts([]) == []


def test_edition_becomes_a_search_dict_with_author() -> None:
    edition = Edition(
        book=Book(title="Bitka na Sutjesci: Pakao u raju", author="Simun Cimerman"),
        bookstore=Bookstore.DELFI,
        availability=Availability.AVAILABLE,
        price_rsd=1500,
        language="Serbian",
        url="https://delfi.rs/knjige/246557-x.html",
    )

    assert editions_to_search_dicts([edition]) == [
        {"title": "Bitka na Sutjesci: Pakao u raju", "author_name": ["Simun Cimerman"]}
    ]


def test_edition_with_no_author_omits_author_name() -> None:
    edition = Edition(
        book=Book(title="No Author Book", author=""),
        bookstore=Bookstore.DELFI,
        availability=Availability.NOT_AVAILABLE,
        language="Serbian",
        url="https://delfi.rs/knjige/y.html",
    )

    assert editions_to_search_dicts([edition]) == [{"title": "No Author Book", "author_name": []}]


def test_books_to_search_dicts_empty_list_returns_empty() -> None:
    assert books_to_search_dicts([]) == []


def test_books_to_search_dicts_includes_author() -> None:
    book = Book(title="Leto bez muskaraca", author="Siri Hustvedt")
    assert books_to_search_dicts([book]) == [
        {"title": "Leto bez muskaraca", "author_name": ["Siri Hustvedt"]}
    ]


@pytest.mark.asyncio
async def test_search_booka_books_returns_search_dicts_without_resolving_author() -> None:
    # Discovery search (unlike find_editions) never resolves author — it's
    # a raw pass-through of the search endpoint's own results, same as
    # search_delfi_books.
    search_result = [
        {
            "name": "Brana na Atlantiku",
            "permalink": "https://booka.rs/knjige/savremena-knjizevnost/brana-na-atlantiku/",
            "is_in_stock": True,
            "is_purchasable": True,
            "prices": {"price": "89100", "currency_minor_unit": 2},
            "attributes": [],
        }
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=json.dumps(search_result))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        results = await search_booka_books("Brana na Atlantiku", http_client)

    assert results == [{"title": "Brana na Atlantiku", "author_name": []}]
