import json

import httpx
import pytest

from book_finder.domain.models import Availability, Book, Bookstore, Edition
from book_finder.search.store_search import (
    books_to_search_dicts,
    editions_to_search_dicts,
    search_booka_books,
    search_delfi_books,
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

    assert editions_to_search_dicts([edition]) == [
        {"title": "No Author Book", "author_name": []}
    ]


def test_books_to_search_dicts_empty_list_returns_empty() -> None:
    assert books_to_search_dicts([]) == []


def test_books_to_search_dicts_includes_author() -> None:
    book = Book(title="Leto bez muskaraca", author="Siri Hustvedt")
    assert books_to_search_dicts([book]) == [
        {"title": "Leto bez muskaraca", "author_name": ["Siri Hustvedt"]}
    ]


def _booka_handler(*, search_body=None, product_body=None, pisac_body=None):
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "wc/store/v1/products" in url:
            return httpx.Response(
                200, text=json.dumps(search_body if search_body is not None else [])
            )
        if "wp/v2/product" in url:
            return httpx.Response(
                200, text=json.dumps(product_body if product_body is not None else [])
            )
        if "wp/v2/pisac" in url:
            return httpx.Response(
                200, text=json.dumps(pisac_body if pisac_body is not None else {})
            )
        return httpx.Response(404)

    return handler


@pytest.mark.asyncio
async def test_search_booka_books_resolves_author_for_matching_title() -> None:
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
    handler = _booka_handler(
        search_body=search_result,
        product_body=[{"pisac": [215]}],
        pisac_body={"name": "Frederik Begbede"},
    )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        results = await search_booka_books("Brana na Atlantiku", http_client)

    assert results == [
        {"title": "Brana na Atlantiku", "author_name": ["Frederik Begbede"]}
    ]


def _delfi_search_response(results: list[dict]) -> str:
    return json.dumps({"data": {"results": results}})


@pytest.mark.asyncio
async def test_search_delfi_books_excludes_titles_unrelated_to_the_query() -> None:
    matching_result = {
        "oldProductId": 1,
        "title": "Malo zivota",
        "authors": [{"authorName": "Hanja Janagihara"}],
        "isAvailable": True,
        "priceList": {"regularDiscountPrice": 1500},
        "cover": "Mek",
    }
    unrelated_result = {
        "oldProductId": 2,
        "title": "The Facts of Destruction",
        "authors": [{"authorName": "Rostislav Kocourek"}],
        "isAvailable": True,
        "priceList": {"regularDiscountPrice": 1000},
        "cover": "Mek",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, text=_delfi_search_response([matching_result, unrelated_result])
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        results = await search_delfi_books("Malo zivota", http_client)

    assert results == [
        {"title": "Malo zivota", "author_name": ["Hanja Janagihara"]}
    ]


@pytest.mark.asyncio
async def test_search_booka_books_excludes_titles_unrelated_to_the_query() -> None:
    search_result = [
        {
            "name": "Brana na Atlantiku",
            "permalink": "https://booka.rs/knjige/savremena-knjizevnost/brana-na-atlantiku/",
            "is_in_stock": True,
            "is_purchasable": True,
            "prices": {"price": "89100", "currency_minor_unit": 2},
            "attributes": [],
        },
        {
            "name": "The Facts of Destruction",
            "permalink": "https://booka.rs/knjige/eseji/the-facts-of-destruction/",
            "is_in_stock": True,
            "is_purchasable": True,
            "prices": {"price": "150000", "currency_minor_unit": 2},
            "attributes": [],
        },
    ]
    handler = _booka_handler(
        search_body=search_result,
        product_body=[{"pisac": [215]}],
        pisac_body={"name": "Frederik Begbede"},
    )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        results = await search_booka_books("Brana na Atlantiku", http_client)

    assert results == [
        {"title": "Brana na Atlantiku", "author_name": ["Frederik Begbede"]}
    ]
