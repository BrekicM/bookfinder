from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from book_finder.config import settings
from book_finder.domain.models import Book
from book_finder.web.redirects import DEFAULT_REDIRECT, safe_redirect_target
from book_finder.web.render import render
from book_finder.wishlist.storage import add_book, list_books, remove_book

router = APIRouter()


@router.get("/wishlist", response_class=HTMLResponse)
async def wishlist_page(request: Request) -> HTMLResponse:
    books = list_books(settings.wishlist_file)
    return render(request, "wishlist.html", {"books": books})


@router.post("/wishlist/add", response_class=RedirectResponse)
async def wishlist_add(
    title: str = Form(...),
    author: str = Form(""),
    next_url: str = Form(DEFAULT_REDIRECT, alias="next"),
) -> RedirectResponse:
    add_book(settings.wishlist_file, Book(title=title, author=author))
    return RedirectResponse(url=safe_redirect_target(next_url), status_code=303)


@router.post("/wishlist/remove", response_class=RedirectResponse)
async def wishlist_remove(
    title: str = Form(...),
    author: str = Form(""),
    next_url: str = Form(DEFAULT_REDIRECT, alias="next"),
) -> RedirectResponse:
    remove_book(settings.wishlist_file, Book(title=title, author=author))
    return RedirectResponse(url=safe_redirect_target(next_url), status_code=303)
