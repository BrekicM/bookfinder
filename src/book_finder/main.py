from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from book_finder.web.language_middleware import LanguageMiddleware
from book_finder.web.routes_book import router as book_router
from book_finder.web.routes_browse import router as browse_router
from book_finder.web.routes_search import router as search_router
from book_finder.web.routes_wishlist import router as wishlist_router

STATIC_DIR = Path(__file__).parent / "web" / "static"

app = FastAPI(title="Book Finder")
app.add_middleware(LanguageMiddleware)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(browse_router)
app.include_router(book_router)
app.include_router(search_router)
app.include_router(wishlist_router)
