from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from book_finder.search.open_library_search import search_open_library
from book_finder.search.resolver import resolve

router = APIRouter()
templates = Jinja2Templates(directory="src/book_finder/web/templates")


@router.get("/search", response_model=None)
async def search(request: Request, q: str) -> HTMLResponse | RedirectResponse:
    async with httpx.AsyncClient() as http_client:
        resolution = await resolve(q, lambda query: search_open_library(query, http_client))

    if resolution.kind == "single":
        book = resolution.book
        query_string = urlencode({"title": book.title, "author": book.author})
        return RedirectResponse(url=f"/books?{query_string}")

    return templates.TemplateResponse(
        request, "search_results.html", {"query": q, "candidates": resolution.candidates}
    )
