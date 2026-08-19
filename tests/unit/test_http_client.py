# Test list:
# - every outbound request carries the identifying BookFinder User-Agent
# - the app owns one pooled client for its whole lifetime
# - the search route is handed the app's client, not one of its own
# - the book-detail route is handed the same client
# - the browse route is handed the same client
# - the same instance survives across separate requests (nothing is rebuilt per request)

import httpx
from fastapi.testclient import TestClient

from book_finder.domain.models import Book
from book_finder.main import app
from book_finder.stores import registry
from book_finder.web import routes_browse
from book_finder.web.http_client import create_http_client


def test_outbound_requests_carry_the_book_finder_user_agent() -> None:
    # ADR 0008 has this project excluding Dereta on robots.txt grounds, so
    # identifying ourselves to every store — not just one — is the intent.
    http_client = create_http_client()

    request = http_client.build_request("GET", "https://example.com/whatever")

    assert "BookFinder" in request.headers["User-Agent"]


def test_app_owns_one_pooled_client_for_its_lifetime(client: TestClient) -> None:
    assert isinstance(app.state.http_client, httpx.AsyncClient)


def _record_client_seen_by_search(monkeypatch, seen: list[httpx.AsyncClient]) -> None:
    for store_client in registry.ACTIVE_CLIENTS:

        async def search_titles(query, http_client) -> list[Book]:
            seen.append(http_client)
            return []

        monkeypatch.setattr(store_client, "search_titles", search_titles)


def _record_client_seen_by_book_detail(monkeypatch, seen: list[httpx.AsyncClient]) -> None:
    for store_client in registry.ACTIVE_CLIENTS:

        async def find_editions(book, http_client) -> list:
            seen.append(http_client)
            return []

        monkeypatch.setattr(store_client, "find_editions", find_editions)


def test_search_route_uses_the_apps_pooled_client(client: TestClient, monkeypatch) -> None:
    seen: list[httpx.AsyncClient] = []
    _record_client_seen_by_search(monkeypatch, seen)

    async def no_open_library(query, http_client) -> list[dict]:
        return []

    monkeypatch.setattr("book_finder.web.routes_search.search_open_library", no_open_library)

    client.get("/search", params={"q": "anything"})

    assert seen
    assert all(http_client is app.state.http_client for http_client in seen)


def test_book_detail_route_uses_the_apps_pooled_client(client: TestClient, monkeypatch) -> None:
    seen: list[httpx.AsyncClient] = []
    _record_client_seen_by_book_detail(monkeypatch, seen)

    client.get("/books", params={"title": "1984", "author": "George Orwell"})

    assert seen
    assert all(http_client is app.state.http_client for http_client in seen)


def test_browse_route_uses_the_apps_pooled_client(client: TestClient, monkeypatch) -> None:
    seen: list[httpx.AsyncClient] = []

    async def fake_get_lists(genre, http_client, **kwargs) -> tuple[list, list]:
        seen.append(http_client)
        return [], []

    monkeypatch.setattr(routes_browse, "get_lists", fake_get_lists)

    client.get("/genres/fiction")

    assert seen == [app.state.http_client]


def test_the_same_client_is_reused_across_requests(client: TestClient, monkeypatch) -> None:
    # The point of pooling: two requests must not each pay a fresh TCP+TLS
    # handshake to the same handful of stores.
    seen: list[httpx.AsyncClient] = []
    _record_client_seen_by_book_detail(monkeypatch, seen)

    client.get("/books", params={"title": "1984", "author": "George Orwell"})
    first_request_clients = list(seen)
    client.get("/books", params={"title": "Dune", "author": "Frank Herbert"})

    assert first_request_clients
    assert len(seen) > len(first_request_clients)
    assert all(http_client is first_request_clients[0] for http_client in seen)
