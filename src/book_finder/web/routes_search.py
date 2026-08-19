import asyncio
from collections.abc import Awaitable
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from book_finder.search.open_library_search import search_open_library
from book_finder.search.resolver import resolve
from book_finder.search.store_search import (
    books_to_search_dicts,
    search_booka_books,
    search_delfi_books,
)
from book_finder.stores.base import BookstoreClient
from book_finder.stores.registry import CATALOG_SEARCH_CLIENTS
from book_finder.web.render import render

router = APIRouter()


async def _safe(source: Awaitable[list[dict]]) -> list[dict]:
    try:
        return await source
    except httpx.HTTPError:
        return []


async def _safe_catalog_search(
    client: BookstoreClient, query: str, http_client: httpx.AsyncClient
) -> list[dict]:
    try:
        books = await client.search_titles(query, http_client)
    except httpx.HTTPError:
        return []
    return books_to_search_dicts(books)


@router.get("/search", response_model=None)
async def search(request: Request, q: str) -> HTMLResponse | RedirectResponse:
    async with httpx.AsyncClient() as http_client:
        results = await asyncio.gather(
            _safe(search_delfi_books(q, http_client)),
            _safe(search_booka_books(q, http_client)),
            *(
                _safe_catalog_search(client, q, http_client)
                for client in CATALOG_SEARCH_CLIENTS
            ),
            _safe(search_open_library(q, http_client)),
        )

    # Store-native results (purchasable in Serbia, this app's core purpose)
    # go first so they survive resolve()'s MAX_CANDIDATES truncation — Open
    # Library alone can return more than that for an internationally popular
    # title, in editions/translations that aren't actually buyable here.
    combined = [result for source_results in results for result in source_results]

    async def combined_search(query: str) -> list[dict]:
        return combined

    resolution = await resolve(q, combined_search)

    if resolution.kind == "single":
        book = resolution.book
        query_string = urlencode({"title": book.title, "author": book.author})
        return RedirectResponse(url=f"/books?{query_string}")

    return render(
        request,
        "search_results.html",
        {"query": q, "candidates": resolution.candidates},
    )
