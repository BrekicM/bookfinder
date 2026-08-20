from book_finder.stores.agora import AgoraClient
from book_finder.stores.base import BookstoreClient, CatalogBookstoreClient
from book_finder.stores.booka import BookaClient
from book_finder.stores.carobna_knjiga import CarobnaKnjigaClient
from book_finder.stores.delfi import DelfiClient
from book_finder.stores.geopoetika import GeopoetikaClient
from book_finder.stores.registry import ACTIVE_CLIENTS


def test_booka_is_an_active_client() -> None:
    assert any(isinstance(client, BookaClient) for client in ACTIVE_CLIENTS)


def test_agora_is_an_active_client() -> None:
    assert any(isinstance(client, AgoraClient) for client in ACTIVE_CLIENTS)


def test_carobna_knjiga_is_an_active_catalog_client() -> None:
    matches = [client for client in ACTIVE_CLIENTS if isinstance(client, CarobnaKnjigaClient)]
    assert len(matches) == 1
    assert isinstance(matches[0], CatalogBookstoreClient)


def test_geopoetika_is_an_active_catalog_client() -> None:
    matches = [client for client in ACTIVE_CLIENTS if isinstance(client, GeopoetikaClient)]
    assert len(matches) == 1
    assert isinstance(matches[0], CatalogBookstoreClient)


def test_booka_delfi_and_agora_do_not_use_the_sitemap_catalog_search_path() -> None:
    # Booka, Delfi, and Agora have their own live search APIs (ADR 0009 /
    # ADR 0004 / ADR 0012), so they must not inherit the sitemap-catalog
    # machinery. This used to be expressed as a separate CATALOG_SEARCH_CLIENTS
    # list in the registry; now it's a type distinction, so the registry needs
    # only one list.
    for client in ACTIVE_CLIENTS:
        if isinstance(client, BookaClient | DelfiClient | AgoraClient):
            assert not isinstance(client, CatalogBookstoreClient)


def test_every_active_client_satisfies_the_one_bookstore_contract() -> None:
    # The point of the split: search and the live-check page can iterate a
    # single list without asking which kind of store each client is.
    assert ACTIVE_CLIENTS
    for client in ACTIVE_CLIENTS:
        assert isinstance(client, BookstoreClient)
        assert callable(client.find_editions)
        assert callable(client.search_titles)
