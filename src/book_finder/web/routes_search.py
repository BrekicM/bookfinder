import asyncio
from collections.abc import Awaitable
from typing import Annotated
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from book_finder.search.open_library_search import search_open_library
from book_finder.search.resolver import resolve
from book_finder.search.store_search import books_to_search_dicts
from book_finder.stores.base import BookstoreClient
from book_finder.stores.registry import ACTIVE_CLIENTS
from book_finder.web.http_client import get_http_client
from book_finder.web.render import render

router = APIRouter()

OPEN_LIBRARY_SOURCE_NAME = "Open Library"

# A source that failed and one that genuinely found nothing both contribute
# zero results, so the merged list alone cannot tell them apart. Carrying the
# source name alongside a None-on-failure result keeps that distinction, which
# is what lets the page admit the answer is partial instead of presenting a
# short list (or "no matches") as if it were the whole catalogue.
SourceOutcome = tuple[str, list[dict] | None]


async def _safe(name: str, source: Awaitable[list[dict]]) -> SourceOutcome:
    try:
        return name, await source
    except httpx.HTTPError:
        return name, None


async def _safe_store_search(
    client: BookstoreClient, query: str, http_client: httpx.AsyncClient
) -> SourceOutcome:
    """search_titles() wrapped so one store's failure never blanks the search."""
    try:
        books = await client.search_titles(query, http_client)
    except httpx.HTTPError:
        return client.bookstore, None
    return client.bookstore, books_to_search_dicts(books)


@router.get("/search", response_model=None)
async def search(
    request: Request,
    q: str,
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> HTMLResponse | RedirectResponse:
    outcomes = await asyncio.gather(
        *(_safe_store_search(client, q, http_client) for client in ACTIVE_CLIENTS),
        _safe(OPEN_LIBRARY_SOURCE_NAME, search_open_library(q, http_client)),
    )

    # Store-native results (purchasable in Serbia, this app's core purpose)
    # go first so they survive resolve()'s MAX_CANDIDATES truncation — Open
    # Library alone can return more than that for an internationally popular
    # title, in editions/translations that aren't actually buyable here.
    combined = [
        result for _, source_results in outcomes if source_results for result in source_results
    ]
    unreachable_sources = [name for name, source_results in outcomes if source_results is None]

    resolution = resolve(combined)

    if resolution.kind == "single":
        book = resolution.book
        query_string = urlencode({"title": book.title, "author": book.author})
        return RedirectResponse(url=f"/books?{query_string}")

    return render(
        request,
        "search_results.html",
        {
            "query": q,
            "candidates": resolution.candidates,
            "unreachable_sources": unreachable_sources,
        },
    )
