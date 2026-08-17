import httpx

SEARCH_URL = "https://openlibrary.org/search.json"


async def search_open_library(query: str, http_client: httpx.AsyncClient) -> list[dict]:
    response = await http_client.get(
        SEARCH_URL,
        params={"q": query, "fields": "title,author_name,first_publish_year", "limit": 20},
        timeout=8.0,
    )
    response.raise_for_status()
    return response.json().get("docs", [])
