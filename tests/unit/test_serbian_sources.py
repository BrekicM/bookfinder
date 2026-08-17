import httpx
import pytest

from book_finder.domain.models import Genre
from book_finder.popularity.serbian_sources import (
    fetch_serbian_popularity,
    has_serbian_source,
)

LAGUNA_HTML = """
<h2 class="line-clamp-2">Laguna Book One</h2><span class="text-[#4B5563]">Author A</span>
"""

VULKAN_HTML = """
<h1 class="product-list-heading"><span>Top lista ::: Romani</span></h1>
<h3 class="nb-title"><span>Vulkan Book One</span></h3>
<a class="author-name">Author B</a>
"""


def test_has_serbian_source_true_for_fiction() -> None:
    assert has_serbian_source(Genre.FICTION) is True


def test_has_serbian_source_false_for_programming_tech() -> None:
    assert has_serbian_source(Genre.PROGRAMMING_TECH) is False


@pytest.mark.asyncio
async def test_combines_both_stores_and_reranks_sequentially() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "laguna" in str(request.url):
            return httpx.Response(200, text=LAGUNA_HTML)
        return httpx.Response(200, text=VULKAN_HTML)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        entries = await fetch_serbian_popularity(Genre.FICTION, client)

    assert [e.rank for e in entries] == [1, 2]
    assert {e.book.title for e in entries} == {"Laguna Book One", "Vulkan Book One"}


@pytest.mark.asyncio
async def test_returns_partial_results_when_one_store_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "laguna" in str(request.url):
            raise httpx.ConnectError("simulated failure", request=request)
        return httpx.Response(200, text=VULKAN_HTML)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        entries = await fetch_serbian_popularity(Genre.FICTION, client)

    assert len(entries) == 1
    assert entries[0].book.title == "Vulkan Book One"
    assert entries[0].rank == 1


@pytest.mark.asyncio
async def test_raises_when_all_available_stores_fail() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated failure", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(httpx.HTTPError):
            await fetch_serbian_popularity(Genre.FICTION, client)
