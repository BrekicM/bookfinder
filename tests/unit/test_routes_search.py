import logging
import re

import httpx
import pytest
from fastapi.testclient import TestClient

from book_finder.domain.models import Book, Bookstore
from book_finder.i18n.strings import EN
from book_finder.stores import registry
from book_finder.web import routes_search

_OPEN_LIBRARY_TITLE = "Open Library Only Title"


def _stub_store_search(monkeypatch) -> None:
    """Give every active client one distinct, identifiable search result."""
    for store_client in registry.ACTIVE_CLIENTS:

        async def search_titles(query, http_client, *, name=store_client.bookstore):
            return [Book(title=f"{name} Store Title", author=f"{name} Author")]

        monkeypatch.setattr(store_client, "search_titles", search_titles)


async def _stub_open_library(query, http_client) -> list[dict]:
    return [{"title": _OPEN_LIBRARY_TITLE, "author_name": ["OL Author"]}]


def test_store_native_results_precede_open_library_results(client: TestClient, monkeypatch) -> None:
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


@pytest.mark.parametrize("failing_bookstore", [c.bookstore for c in registry.ACTIVE_CLIENTS])
def test_one_store_failing_does_not_blank_the_whole_search(
    client: TestClient, monkeypatch, failing_bookstore: str
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


# Test list — surfacing sources that failed rather than silently shrinking results:
# - a failing store is named in the response as unreachable
# - a failing Open Library is named as "Open Library"
# - all sources healthy: no unreachable notice at all
# - every source failing: the notice appears instead of a bare "no matches"
# - each failure is logged with its exception


def _unreachable_notice(html: str) -> str | None:
    match = re.search(r'<p class="status-failed">(.*?)</p>', html, re.DOTALL)
    return match.group(1).strip() if match else None


def test_failing_store_is_named_as_unreachable(client: TestClient, monkeypatch) -> None:
    _stub_store_search(monkeypatch)
    monkeypatch.setattr(routes_search, "search_open_library", _stub_open_library)

    async def failing_search(query, http_client):
        raise httpx.ConnectError("simulated store outage")

    monkeypatch.setattr(registry._delfi, "search_titles", failing_search)

    response = client.get("/search", params={"q": "anything"})

    assert _unreachable_notice(response.text) is not None
    assert Bookstore.DELFI.value in _unreachable_notice(response.text)


def test_failing_open_library_is_named_as_unreachable(client: TestClient, monkeypatch) -> None:
    _stub_store_search(monkeypatch)

    async def failing_open_library(query, http_client):
        raise httpx.ConnectTimeout("simulated Open Library outage")

    monkeypatch.setattr(routes_search, "search_open_library", failing_open_library)

    response = client.get("/search", params={"q": "anything"})

    assert _unreachable_notice(response.text) is not None
    assert routes_search.OPEN_LIBRARY_SOURCE_NAME in _unreachable_notice(response.text)


def test_does_not_claim_no_matches_when_every_source_failed(
    client: TestClient, monkeypatch
) -> None:
    # "No matches found" is a claim about the catalogues, and nothing answered,
    # so the app is in no position to make it.
    async def failing_search(query, http_client):
        raise httpx.ConnectError("simulated outage")

    for store_client in registry.ACTIVE_CLIENTS:
        monkeypatch.setattr(store_client, "search_titles", failing_search)
    monkeypatch.setattr(routes_search, "search_open_library", failing_search)

    response = client.get("/search", params={"q": "anything"})

    assert _unreachable_notice(response.text) is not None
    assert EN["no_matches"] not in response.text


def test_source_failure_is_logged_with_its_exception(
    client: TestClient, monkeypatch, caplog
) -> None:
    # The notice tells the user a source is down; the log is what tells us why.
    _stub_store_search(monkeypatch)

    async def failing_open_library(query, http_client):
        raise httpx.ConnectTimeout("openlibrary.org did not answer")

    monkeypatch.setattr(routes_search, "search_open_library", failing_open_library)

    with caplog.at_level(logging.WARNING, logger=routes_search.__name__):
        client.get("/search", params={"q": "anything"})

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    message = warnings[0].getMessage()
    assert routes_search.OPEN_LIBRARY_SOURCE_NAME in message
    assert "openlibrary.org did not answer" in message
    assert warnings[0].exc_info is not None


def test_store_failure_is_logged_with_its_exception(
    client: TestClient, monkeypatch, caplog
) -> None:
    _stub_store_search(monkeypatch)
    monkeypatch.setattr(routes_search, "search_open_library", _stub_open_library)

    async def failing_search(query, http_client):
        raise httpx.ConnectError("delfi.rs refused the connection")

    monkeypatch.setattr(registry._delfi, "search_titles", failing_search)

    with caplog.at_level(logging.WARNING, logger=routes_search.__name__):
        client.get("/search", params={"q": "anything"})

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    message = warnings[0].getMessage()
    assert Bookstore.DELFI.value in message
    assert "delfi.rs refused the connection" in message
    assert warnings[0].exc_info is not None
