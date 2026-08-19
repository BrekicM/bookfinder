from datetime import timedelta

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from book_finder.config import settings
from book_finder.domain.models import Genre
from book_finder.popularity.service import get_lists
from book_finder.web.render import render

router = APIRouter()


def genre_translation_key(genre: Genre) -> str:
    return f"genre_{genre.name.lower()}"


GENRE_SLUGS: dict[str, Genre] = {
    "fiction": Genre.FICTION,
    "fantasy": Genre.FANTASY,
    "sci-fi": Genre.SCI_FI,
    "mystery-thriller": Genre.MYSTERY_THRILLER,
    "romance": Genre.ROMANCE,
    "non-fiction": Genre.NON_FICTION,
    "young-adult": Genre.YOUNG_ADULT,
    "childrens": Genre.CHILDRENS,
    "programming-tech": Genre.PROGRAMMING_TECH,
}


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return render(request, "home.html", {"genre_slugs": GENRE_SLUGS})


@router.get("/genres/{genre_slug}", response_class=HTMLResponse)
async def genre_page(request: Request, genre_slug: str) -> HTMLResponse:
    genre = GENRE_SLUGS.get(genre_slug)
    if genre is None:
        raise HTTPException(status_code=404, detail="Unknown genre")

    async with httpx.AsyncClient() as http_client:
        global_list, serbian_list = await get_lists(
            genre,
            http_client,
            cache_dir=settings.cache_dir,
            cache_ttl=timedelta(hours=settings.popularity_cache_ttl_hours),
        )

    return render(
        request,
        "genre.html",
        {
            "genre": genre,
            "genre_slugs": GENRE_SLUGS,
            "global_list": global_list,
            "serbian_list": serbian_list,
        },
    )
