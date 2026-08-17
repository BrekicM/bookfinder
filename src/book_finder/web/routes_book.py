import asyncio

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from book_finder.domain.models import Book
from book_finder.stores.base import safe_find_editions
from book_finder.stores.registry import ACTIVE_CLIENTS

router = APIRouter()
templates = Jinja2Templates(directory="src/book_finder/web/templates")

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BookFinder/0.1; personal use)"}


@router.get("/books", response_class=HTMLResponse)
async def book_detail(request: Request, title: str, author: str = "") -> HTMLResponse:
    book = Book(title=title, author=author)

    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True) as http_client:
        results = await asyncio.gather(
            *(safe_find_editions(client, book, http_client) for client in ACTIVE_CLIENTS)
        )

    return templates.TemplateResponse(
        request, "book_detail.html", {"book": book, "results": results}
    )
