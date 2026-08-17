from datetime import timedelta

import httpx
import pytest

from book_finder.domain.models import Book, Genre, PopularityEntry
from book_finder.popularity.service import get_popularity_list

ENTRIES = [PopularityEntry(book=Book(title="Some Book", author=""), rank=1, source="Test")]


async def _fetch_ok() -> list[PopularityEntry]:
    return ENTRIES


async def _fetch_fails() -> list[PopularityEntry]:
    raise httpx.ConnectError("simulated failure")


@pytest.mark.asyncio
async def test_fetches_and_caches_when_no_cache_exists(tmp_path) -> None:
    result = await get_popularity_list(
        genre=Genre.FICTION,
        scope="global",
        cache_key="test_key_1",
        fetch=_fetch_ok,
        cache_dir=tmp_path,
        cache_ttl=timedelta(hours=1),
    )

    assert result.available is True
    assert result.scope == "global"
    assert result.genre == Genre.FICTION
    assert [e.book.title for e in result.entries] == ["Some Book"]


@pytest.mark.asyncio
async def test_uses_cache_without_calling_fetch_when_fresh(tmp_path) -> None:
    calls = 0

    async def counting_fetch() -> list[PopularityEntry]:
        nonlocal calls
        calls += 1
        return ENTRIES

    await get_popularity_list(
        genre=Genre.FICTION,
        scope="global",
        cache_key="test_key_2",
        fetch=counting_fetch,
        cache_dir=tmp_path,
        cache_ttl=timedelta(hours=1),
    )
    assert calls == 1

    result = await get_popularity_list(
        genre=Genre.FICTION,
        scope="global",
        cache_key="test_key_2",
        fetch=counting_fetch,
        cache_dir=tmp_path,
        cache_ttl=timedelta(hours=1),
    )
    assert calls == 1  # not called again — served from cache
    assert [e.book.title for e in result.entries] == ["Some Book"]


@pytest.mark.asyncio
async def test_unavailable_when_fetch_fails_and_no_cache(tmp_path) -> None:
    result = await get_popularity_list(
        genre=Genre.PROGRAMMING_TECH,
        scope="serbian",
        cache_key="test_key_3",
        fetch=_fetch_fails,
        cache_dir=tmp_path,
        cache_ttl=timedelta(hours=1),
    )

    assert result.available is False
    assert result.entries == []


@pytest.mark.asyncio
async def test_serves_stale_cache_when_fetch_fails(tmp_path) -> None:
    await get_popularity_list(
        genre=Genre.FICTION,
        scope="global",
        cache_key="test_key_4",
        fetch=_fetch_ok,
        cache_dir=tmp_path,
        cache_ttl=timedelta(seconds=0),  # immediately stale
    )

    result = await get_popularity_list(
        genre=Genre.FICTION,
        scope="global",
        cache_key="test_key_4",
        fetch=_fetch_fails,
        cache_dir=tmp_path,
        cache_ttl=timedelta(seconds=0),
    )

    assert result.available is True
    assert [e.book.title for e in result.entries] == ["Some Book"]
