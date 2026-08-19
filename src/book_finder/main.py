from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from book_finder.web.http_client import create_http_client
from book_finder.web.language_middleware import LanguageMiddleware
from book_finder.web.routes_book import router as book_router
from book_finder.web.routes_browse import router as browse_router
from book_finder.web.routes_search import router as search_router
from book_finder.web.routes_wishlist import router as wishlist_router

STATIC_DIR = Path(__file__).parent / "web" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Own one pooled outbound HTTP client for the app's whole lifetime."""
    app.state.http_client = create_http_client()
    try:
        yield
    finally:
        await app.state.http_client.aclose()
        # Clear it rather than leaving a closed client behind: an app that was
        # never started (or was already shut down) must fail loudly instead of
        # quietly serving requests through a dead connection pool.
        del app.state.http_client


app = FastAPI(title="Book Finder", lifespan=lifespan)
app.add_middleware(LanguageMiddleware)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(browse_router)
app.include_router(book_router)
app.include_router(search_router)
app.include_router(wishlist_router)
