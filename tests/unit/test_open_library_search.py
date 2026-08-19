import httpx
import pytest

from book_finder.search.open_library_search import search_open_library


@pytest.mark.asyncio
async def test_search_open_library_excludes_titles_unrelated_to_the_query() -> None:
    response_body = {
        "docs": [
            {
                "title": "Malo zivota",
                "author_name": ["Hanja Janagihara"],
                "first_publish_year": 2015,
            },
            {
                "title": "The Facts of Destruction of Oriental and Occidental spiritual teachings.",
                "author_name": ["Rostislav Kocourek"],
                "first_publish_year": 1970,
            },
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_body)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        results = await search_open_library("Malo zivota", http_client)

    assert results == [
        {
            "title": "Malo zivota",
            "author_name": ["Hanja Janagihara"],
            "first_publish_year": 2015,
        }
    ]


@pytest.mark.asyncio
async def test_search_open_library_matches_by_author_with_no_title_overlap() -> None:
    response_body = {
        "docs": [
            {
                "title": "21 zlatna poluga",
                "author_name": ["Nenad Gugl"],
                "first_publish_year": 2020,
            }
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_body)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        results = await search_open_library("Nenad Gugl", http_client)

    assert results == response_body["docs"]


@pytest.mark.asyncio
async def test_search_open_library_returns_empty_when_no_docs_match() -> None:
    response_body = {
        "docs": [{"title": "Completely Different Book", "author_name": ["Someone Else"]}]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_body)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        results = await search_open_library("Malo zivota", http_client)

    assert results == []
