import asyncio
from collections.abc import Awaitable
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from book_finder.search.open_library_search import search_open_library
from book_finder.search.resolver import resolve
from book_finder.search.store_search import search_delfi_books

router = APIRouter()
templates = Jinja2Templates(directory="src/book_finder/web/templates")


async def _safe(source: Awaitable[list[dict]]) -> list[dict]:
    try:
        return await source
    except httpx.HTTPError:
        return []


@router.get("/search", response_model=None)
async def search(request: Request, q: str) -> HTMLResponse | RedirectResponse:
    async with httpx.AsyncClient() as http_client:
        open_library_results, delfi_results = await asyncio.gather(
            _safe(search_open_library(q, http_client)),
            _safe(search_delfi_books(q, http_client)),
        )

    combined = open_library_results + delfi_results

    async def combined_search(query: str) -> list[dict]:
        return combined

    resolution = await resolve(q, combined_search)

    if resolution.kind == "single":
        book = resolution.book
        query_string = urlencode({"title": book.title, "author": book.author})
        return RedirectResponse(url=f"/books?{query_string}")

    return templates.TemplateResponse(
        request, "search_results.html", {"query": q, "candidates": resolution.candidates}
    )
