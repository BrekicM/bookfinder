import asyncio
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from book_finder.config import settings
from book_finder.domain.models import Book
from book_finder.stores.base import safe_find_editions
from book_finder.stores.registry import ACTIVE_CLIENTS
from book_finder.web.http_client import get_http_client
from book_finder.web.render import render
from book_finder.wishlist.storage import is_in_wishlist

router = APIRouter()


@router.get("/books", response_class=HTMLResponse)
async def book_detail(
    request: Request,
    title: str,
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
    author: str = "",
) -> HTMLResponse:
    book = Book(title=title, author=author)

    results = await asyncio.gather(
        *(safe_find_editions(client, book, http_client) for client in ACTIVE_CLIENTS)
    )

    in_wishlist = is_in_wishlist(settings.wishlist_file, book)

    return render(
        request,
        "book_detail.html",
        {"book": book, "results": results, "in_wishlist": in_wishlist},
    )
