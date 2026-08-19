from book_finder.stores.booka import BookaClient
from book_finder.stores.delfi import DelfiClient
from book_finder.stores.registry import ACTIVE_CLIENTS, CATALOG_SEARCH_CLIENTS


def test_booka_is_an_active_client() -> None:
    assert any(isinstance(client, BookaClient) for client in ACTIVE_CLIENTS)


def test_booka_is_not_a_catalog_search_client() -> None:
    # Booka has its own live search API (see ADR 0009), same reasoning as
    # Delfi's exclusion from the sitemap-catalog search path.
    assert not any(isinstance(client, BookaClient) for client in CATALOG_SEARCH_CLIENTS)
    assert not any(isinstance(client, DelfiClient) for client in CATALOG_SEARCH_CLIENTS)
