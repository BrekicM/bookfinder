import asyncio
from collections.abc import Awaitable
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from book_finder.search.open_library_search import search_open_library
from book_finder.search.resolver import resolve
from book_finder.search.store_search import books_to_search_dicts
from book_finder.stores.base import BookstoreClient
from book_finder.stores.registry import ACTIVE_CLIENTS
from book_finder.web.render import render

router = APIRouter()


async def _safe(source: Awaitable[list[dict]]) -> list[dict]:
    try:
        return await source
    except httpx.HTTPError:
        return []


async def _safe_store_search(
    client: BookstoreClient, query: str, http_client: httpx.AsyncClient
) -> list[dict]:
    """search_titles() wrapped so one store's failure never blanks the search."""
    try:
        books = await client.search_titles(query, http_client)
    except httpx.HTTPError:
        return []
    return books_to_search_dicts(books)


@router.get("/search", response_model=None)
async def search(request: Request, q: str) -> HTMLResponse | RedirectResponse:
    async with httpx.AsyncClient() as http_client:
        results = await asyncio.gather(
            *(_safe_store_search(client, q, http_client) for client in ACTIVE_CLIENTS),
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
