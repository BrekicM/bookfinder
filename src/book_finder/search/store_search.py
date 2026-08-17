import httpx

from book_finder.domain.models import Edition
from book_finder.stores.delfi import build_search_url, parse_search_results


def editions_to_search_dicts(editions: list[Edition]) -> list[dict]:
    return [
        {
            "title": edition.book.title,
            "author_name": [edition.book.author] if edition.book.author else [],
        }
        for edition in editions
    ]


async def search_delfi_books(query: str, http_client: httpx.AsyncClient) -> list[dict]:
    url = build_search_url(query)
    response = await http_client.get(url, timeout=8.0)
    response.raise_for_status()
    return editions_to_search_dicts(parse_search_results(response.text))
