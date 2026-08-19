import json

import httpx
import pytest

from book_finder.domain.models import Book
from book_finder.stores.booka import BookaClient

_SEARCH_RESULT = {
    "name": "Brana na Atlantiku",
    "permalink": "https://booka.rs/knjige/savremena-knjizevnost/brana-na-atlantiku/",
    "is_in_stock": True,
    "is_purchasable": True,
    "prices": {"price": "89100", "currency_minor_unit": 2},
    "attributes": [
        {"name": "Povez", "terms": [{"name": "mek"}]},
        {"name": "Pismo", "terms": [{"name": "latinica"}]},
    ],
}

_OUT_OF_STOCK_RESULT = {
    "name": "Matching Title",
    "permalink": "https://booka.rs/knjige/genre/matching-title/",
    "is_in_stock": False,
    "is_purchasable": True,
    "prices": {"price": "150000", "currency_minor_unit": 2},
    "attributes": [],
}

_PRODUCT_RESPONSE = [{"pisac": [215]}]
_PISAC_RESPONSE = {"name": "Frederik Begbede"}
_EMPTY_PRODUCT_RESPONSE: list = []
_NO_PISAC_PRODUCT_RESPONSE = [{"pisac": []}]


def _handler(*, search_body: list | None = None, product_body=None, pisac_body=None):
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
async def test_find_editions_excludes_matched_but_out_of_stock_results() -> None:
    handler = _handler(search_body=[_OUT_OF_STOCK_RESULT])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        book = Book(title="Matching Title", author="Some Author")
        editions = await BookaClient().find_editions(book, http_client)

    # Out-of-stock candidates must never be resolved for author (wasted
    # calls) or surfaced, mirroring ADR 0002 (Delfi/Laguna/Vulkan).
    assert editions == []


@pytest.mark.asyncio
async def test_search_titles_returns_book_even_when_out_of_stock() -> None:
    # search_titles() is discovery, not an availability check — a Book stays
    # findable when out of stock, unlike find_editions() (ADR 0002).
    handler = _handler(
        search_body=[_OUT_OF_STOCK_RESULT],
        product_body=_PRODUCT_RESPONSE,
        pisac_body=_PISAC_RESPONSE,
    )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        books = await BookaClient().search_titles("Matching Title", http_client)

    assert books == [Book(title="Matching Title", author="Frederik Begbede")]


@pytest.mark.asyncio
async def test_search_titles_resolves_author_per_candidate() -> None:
    handler = _handler(
        search_body=[_SEARCH_RESULT],
        product_body=_PRODUCT_RESPONSE,
        pisac_body=_PISAC_RESPONSE,
    )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        books = await BookaClient().search_titles("Brana na Atlantiku", http_client)

    assert books == [Book(title="Brana na Atlantiku", author="Frederik Begbede")]


@pytest.mark.asyncio
async def test_search_titles_excludes_titles_unrelated_to_the_query() -> None:
    handler = _handler(
        search_body=[_SEARCH_RESULT],
        product_body=_PRODUCT_RESPONSE,
        pisac_body=_PISAC_RESPONSE,
    )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        books = await BookaClient().search_titles("Nothing Like It", http_client)

    assert books == []


@pytest.mark.asyncio
async def test_find_editions_resolves_author_before_final_match() -> None:
    handler = _handler(
        search_body=[_SEARCH_RESULT],
        product_body=_PRODUCT_RESPONSE,
        pisac_body=_PISAC_RESPONSE,
    )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        book = Book(title="Brana na Atlantiku", author="Frederik Begbede")
        editions = await BookaClient().find_editions(book, http_client)

    assert len(editions) == 1
    assert editions[0].book.author == "Frederik Begbede"
    assert editions[0].book.title == "Brana na Atlantiku"


@pytest.mark.asyncio
async def test_find_editions_excludes_when_title_does_not_match() -> None:
    # Author resolution must never even be attempted for a title mismatch —
    # covered implicitly by asserting no crash/exclusion here since the
    # product/pisac endpoints return empty bodies (would fail the match if
    # ever hit with a real author requirement).
    handler = _handler(search_body=[_SEARCH_RESULT])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        book = Book(title="A Completely Different Book", author="Nobody")
        editions = await BookaClient().find_editions(book, http_client)

    assert editions == []


@pytest.mark.asyncio
async def test_find_editions_excludes_when_author_resolution_fails_and_book_has_author() -> None:
    # Hard requirement: an unresolved author (empty pisac list) must NOT be
    # treated as "any author matches" when the query specifies an author —
    # that fallback is only valid for stores with no author data at all.
    handler = _handler(search_body=[_SEARCH_RESULT], product_body=_NO_PISAC_PRODUCT_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        book = Book(title="Brana na Atlantiku", author="Frederik Begbede")
        editions = await BookaClient().find_editions(book, http_client)

    assert editions == []


@pytest.mark.asyncio
async def test_find_editions_keeps_match_when_book_has_no_author_specified() -> None:
    # When the query itself has no author to verify, an unresolved author
    # must not block an otherwise valid title match.
    handler = _handler(search_body=[_SEARCH_RESULT], product_body=_EMPTY_PRODUCT_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        book = Book(title="Brana na Atlantiku", author="")
        editions = await BookaClient().find_editions(book, http_client)

    assert len(editions) == 1
    assert editions[0].book.author == ""
