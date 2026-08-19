import json

import httpx
import pytest

from book_finder.domain.models import Book
from book_finder.stores.delfi import DelfiClient

_OUT_OF_STOCK_RESPONSE = json.dumps(
    {
        "data": {
            "results": [
                {
                    "oldProductId": 111,
                    "title": "Matching Title",
                    "authors": [{"authorName": "Some Author"}],
                    "isAvailable": False,
                    "priceList": {"regularDiscountPrice": 1500},
                    "cover": "Mek",
                }
            ]
        }
    }
)


@pytest.mark.asyncio
async def test_find_editions_excludes_matched_but_out_of_stock_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_OUT_OF_STOCK_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        book = Book(title="Matching Title", author="Some Author")
        editions = await DelfiClient().find_editions(book, http_client)

    # Same ADR 0002 rule as Laguna/Vulkan: an out-of-stock match must look
    # identical to no match at all, not surface with a null price.
    assert editions == []


@pytest.mark.asyncio
async def test_search_titles_returns_book_even_when_out_of_stock() -> None:
    # search_titles() is discovery, not an availability check — a Book stays
    # findable when out of stock, unlike find_editions() (ADR 0002).
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_OUT_OF_STOCK_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        books = await DelfiClient().search_titles("Matching Title", http_client)

    assert books == [Book(title="Matching Title", author="Some Author")]


_UNRELATED_RESPONSE = json.dumps(
    {
        "data": {
            "results": [
                {
                    "oldProductId": 2,
                    "title": "The Facts of Destruction",
                    "authors": [{"authorName": "Rostislav Kocourek"}],
                    "isAvailable": True,
                    "priceList": {"regularDiscountPrice": 1000},
                    "cover": "Mek",
                }
            ]
        }
    }
)


@pytest.mark.asyncio
async def test_search_titles_excludes_titles_unrelated_to_the_query() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_UNRELATED_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        books = await DelfiClient().search_titles("Malo zivota", http_client)

    assert books == []


_KNJIGA_RESPONSE = json.dumps(
    {
        "data": {
            "results": [
                {
                    "oldProductId": 1,
                    "title": "Hobit",
                    "authors": [{"authorName": "Dzon Ronald Rejel Tolkin"}],
                    "isAvailable": True,
                    "priceList": {"regularDiscountPrice": 1000},
                    "cover": "Mek",
                }
            ]
        }
    }
)
_EMPTY_RESPONSE = json.dumps({"data": {"results": []}})


@pytest.mark.asyncio
async def test_find_editions_searches_the_book_categories_not_all_categories() -> None:
    # The unscoped "Sve kategorije" search is capped and can be crowded out
    # entirely by merchandise (mugs, stickers...) for a heavily-merchandised
    # franchise, hiding real books. find_editions() must search the two book
    # categories specifically, not the all-categories endpoint.
    def handler(request: httpx.Request) -> httpx.Response:
        if "/Knjiga/" in str(request.url):
            return httpx.Response(200, text=_KNJIGA_RESPONSE)
        return httpx.Response(200, text=_EMPTY_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        book = Book(title="Hobit", author="Dzon Ronald Rejel Tolkin")
        editions = await DelfiClient().find_editions(book, http_client)

    assert len(editions) == 1
    assert editions[0].book.title == "Hobit"


@pytest.mark.asyncio
async def test_find_editions_dedupes_the_same_product_found_in_both_categories() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_KNJIGA_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        book = Book(title="Hobit", author="Dzon Ronald Rejel Tolkin")
        editions = await DelfiClient().find_editions(book, http_client)

    assert len(editions) == 1
