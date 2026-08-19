import asyncio

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from book_finder.config import settings
from book_finder.domain.models import Book
from book_finder.stores.base import safe_find_editions
from book_finder.stores.registry import ACTIVE_CLIENTS
from book_finder.web.render import render
from book_finder.wishlist.storage import is_in_wishlist

router = APIRouter()

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BookFinder/0.1; personal use)"}


@router.get("/books", response_class=HTMLResponse)
async def book_detail(request: Request, title: str, author: str = "") -> HTMLResponse:
    book = Book(title=title, author=author)

    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True) as http_client:
        results = await asyncio.gather(
            *(safe_find_editions(client, book, http_client) for client in ACTIVE_CLIENTS)
        )

    in_wishlist = is_in_wishlist(settings.wishlist_file, book)

    return render(
        request,
        "book_detail.html",
        {"book": book, "results": results, "in_wishlist": in_wishlist},
    )
