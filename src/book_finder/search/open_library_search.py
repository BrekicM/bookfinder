import httpx

from book_finder.config import settings
from book_finder.stores.base import matches_query

SEARCH_URL = "https://openlibrary.org/search.json"


async def search_open_library(query: str, http_client: httpx.AsyncClient) -> list[dict]:
    """Free-text search discovery, filtered to titles relevant to the query.

    Open Library's own search ranking can surface docs with little to no
    textual overlap with the query (observed for Serbian-language queries
    it doesn't handle well), so results are filtered the same way as the
    Delfi/Booka discovery paths before being surfaced to the user.
    """
    response = await http_client.get(
        SEARCH_URL,
        params={
            "q": query,
            "fields": "title,author_name,first_publish_year",
            "limit": 20,
        },
        timeout=settings.store_request_timeout_seconds,
    )
    response.raise_for_status()
    docs = response.json().get("docs", [])
    return [
        doc
        for doc in docs
        if doc.get("title") and matches_query(candidate_title=doc["title"], query=query)
    ]
