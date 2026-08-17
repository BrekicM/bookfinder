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
