from collections.abc import Awaitable, Callable
from datetime import timedelta
from pathlib import Path

import httpx

from book_finder.domain.models import Genre, PopularityEntry, PopularityList
from book_finder.popularity.cache import read_cache, read_stale, write_cache
from book_finder.popularity.global_sources import fetch_global_popularity
from book_finder.popularity.serbian_sources import (
    fetch_serbian_popularity,
    has_serbian_source,
)

FetchFn = Callable[[], Awaitable[list[PopularityEntry]]]


async def get_popularity_list(
    *,
    genre: Genre,
    scope: str,
    cache_key: str,
    fetch: FetchFn,
    cache_dir: Path,
    cache_ttl: timedelta,
) -> PopularityList:
    cached = read_cache(cache_dir, cache_key, max_age=cache_ttl)
    if cached is not None:
        entries = [PopularityEntry.model_validate(e) for e in cached]
        return PopularityList(genre=genre, scope=scope, entries=entries, available=True)

    try:
        entries = await fetch()
    except httpx.HTTPError:
        stale = read_stale(cache_dir, cache_key)
        if stale is not None:
            entries = [PopularityEntry.model_validate(e) for e in stale]
            return PopularityList(genre=genre, scope=scope, entries=entries, available=True)
        return PopularityList(genre=genre, scope=scope, entries=[], available=False)

    write_cache(cache_dir, cache_key, [e.model_dump() for e in entries])
    return PopularityList(genre=genre, scope=scope, entries=entries, available=True)


async def get_lists(
    genre: Genre,
    http_client: httpx.AsyncClient,
    *,
    cache_dir: Path,
    cache_ttl: timedelta,
) -> tuple[PopularityList, PopularityList]:
    global_list = await get_popularity_list(
        genre=genre,
        scope="global",
        cache_key=f"global_openlibrary_{genre.value}",
        fetch=lambda: fetch_global_popularity(genre, http_client),
        cache_dir=cache_dir,
        cache_ttl=cache_ttl,
    )

    if not has_serbian_source(genre):
        serbian_list = PopularityList(genre=genre, scope="serbian", entries=[], available=False)
    else:
        serbian_list = await get_popularity_list(
            genre=genre,
            scope="serbian",
            cache_key=f"serbian_{genre.value}",
            fetch=lambda: fetch_serbian_popularity(genre, http_client),
            cache_dir=cache_dir,
            cache_ttl=cache_ttl,
        )

    return global_list, serbian_list
