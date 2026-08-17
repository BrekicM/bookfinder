from fastapi import FastAPI

from book_finder.web.routes_book import router as book_router
from book_finder.web.routes_browse import router as browse_router
from book_finder.web.routes_search import router as search_router

app = FastAPI(title="Book Finder")
app.include_router(browse_router)
app.include_router(book_router)
app.include_router(search_router)
