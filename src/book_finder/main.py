from fastapi import FastAPI

from book_finder.web.routes_book import router as book_router

app = FastAPI(title="Book Finder")
app.include_router(book_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok"}
