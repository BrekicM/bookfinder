from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from book_finder.config import settings
from book_finder.domain.models import Book
from book_finder.wishlist.storage import add_book, list_books, remove_book

router = APIRouter()
templates = Jinja2Templates(directory="src/book_finder/web/templates")


@router.get("/wishlist", response_class=HTMLResponse)
async def wishlist_page(request: Request) -> HTMLResponse:
    books = list_books(settings.wishlist_file)
    return templates.TemplateResponse(request, "wishlist.html", {"books": books})


@router.post("/wishlist/add", response_class=RedirectResponse)
async def wishlist_add(
    title: str = Form(...), author: str = Form(""), next: str = Form("/wishlist")
) -> RedirectResponse:
    add_book(settings.wishlist_file, Book(title=title, author=author))
    return RedirectResponse(url=next, status_code=303)


@router.post("/wishlist/remove", response_class=RedirectResponse)
async def wishlist_remove(
    title: str = Form(...), author: str = Form(""), next: str = Form("/wishlist")
) -> RedirectResponse:
    remove_book(settings.wishlist_file, Book(title=title, author=author))
    return RedirectResponse(url=next, status_code=303)
