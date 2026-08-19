import httpx
import pytest
from fastapi.testclient import TestClient

from book_finder.domain.models import Book
from book_finder.main import app
from book_finder.stores import registry
from book_finder.web import routes_search

client = TestClient(app)

_OPEN_LIBRARY_TITLE = "Open Library Only Title"


def _stub_store_search(monkeypatch) -> None:
    """Give every active client one distinct, identifiable search result."""
    for store_client in registry.ACTIVE_CLIENTS:

        async def search_titles(query, http_client, *, name=store_client.bookstore):
            return [Book(title=f"{name} Store Title", author=f"{name} Author")]

        monkeypatch.setattr(store_client, "search_titles", search_titles)


async def _stub_open_library(query, http_client) -> list[dict]:
    return [{"title": _OPEN_LIBRARY_TITLE, "author_name": ["OL Author"]}]


def test_store_native_results_precede_open_library_results(monkeypatch) -> None:
    # The load-bearing invariant, not any particular store order: resolve()
    # truncates at MAX_CANDIDATES, and Open Library alone can exceed that for
    # an internationally popular title — in editions that aren't actually
    # buyable in Serbia. If OL results were interleaved or came first, they
    # could crowd out every purchasable result. Reordering the stores among
    # themselves is fine; letting OL float ahead of any of them is not.
    _stub_store_search(monkeypatch)
    monkeypatch.setattr(routes_search, "search_open_library", _stub_open_library)

    response = client.get("/search", params={"q": "anything"})

    assert response.status_code == 200
    open_library_position = response.text.index(_OPEN_LIBRARY_TITLE)
    for store_client in registry.ACTIVE_CLIENTS:
        title = f"{store_client.bookstore} Store Title"
        assert title in response.text, f"{store_client.bookstore} contributed nothing"
        assert response.text.index(title) < open_library_position


@pytest.mark.parametrize(
    "failing_bookstore", [c.bookstore for c in registry.ACTIVE_CLIENTS]
)
def test_one_store_failing_does_not_blank_the_whole_search(
    monkeypatch, failing_bookstore: str
) -> None:
    _stub_store_search(monkeypatch)
    monkeypatch.setattr(routes_search, "search_open_library", _stub_open_library)

    for store_client in registry.ACTIVE_CLIENTS:
        if store_client.bookstore != failing_bookstore:
            continue

        async def failing_search(query, http_client):
            raise httpx.ConnectError("simulated store outage")

        monkeypatch.setattr(store_client, "search_titles", failing_search)

    response = client.get("/search", params={"q": "anything"})

    assert response.status_code == 200
    assert f"{failing_bookstore} Store Title" not in response.text
    assert _OPEN_LIBRARY_TITLE in response.text
    for store_client in registry.ACTIVE_CLIENTS:
        if store_client.bookstore == failing_bookstore:
            continue
        assert f"{store_client.bookstore} Store Title" in response.text
