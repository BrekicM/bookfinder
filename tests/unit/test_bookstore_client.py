import httpx
import pytest

from book_finder.domain.models import Availability, Book, Bookstore, Edition
from book_finder.stores.base import CatalogBookstoreClient, safe_find_editions


class _AlwaysFailsClient(CatalogBookstoreClient):
    bookstore = "TestStore"
    sitemap_url = "https://example.invalid/sitemap.xml"
    cache_key = "test_always_fails"

    def _parse_product_page(self, html: str) -> Edition | None:
        return None


def _failing_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated network failure", request=request)

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_total_catalog_failure_surfaces_as_error_not_empty_result(
    tmp_path, monkeypatch
) -> None:
    from book_finder import config

    monkeypatch.setattr(config.settings, "cache_dir", tmp_path)

    async with httpx.AsyncClient(transport=_failing_transport()) as http_client:
        book = Book(title="Anything", author="Anyone")
        result = await safe_find_editions(_AlwaysFailsClient(), book, http_client)

    # A total fetch failure must be reported as a failed check, never silently
    # collapsed into "checked fine, just not available" (see base.py's
    # _get_catalog: this exact scenario used to swallow the error and return []).
    assert result.status == "error"
    assert result.editions == []


_SITEMAP_XML = """<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://example.invalid/books/matching-title/</loc></url>
</urlset>"""


class _MatchesButOutOfStockClient(CatalogBookstoreClient):
    bookstore = "TestStore"
    sitemap_url = "https://example.invalid/sitemap.xml"
    cache_key = "test_out_of_stock"

    def _parse_product_page(self, html: str) -> Edition | None:
        # Real-world case: the store carries the title (matches_book passes)
        # but it's out of stock — price_rsd is None, per the Edition model's
        # "None when not available" contract.
        return Edition(
            book=Book(title="Matching Title", author="Some Author"),
            bookstore=Bookstore.LAGUNA,
            availability=Availability.NOT_AVAILABLE,
            price_rsd=None,
            language="Serbian",
            url="https://example.invalid/books/matching-title/",
        )


@pytest.mark.asyncio
async def test_find_editions_excludes_matched_but_out_of_stock_editions(
    tmp_path, monkeypatch
) -> None:
    from book_finder import config

    monkeypatch.setattr(config.settings, "cache_dir", tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        if "sitemap" in str(request.url):
            return httpx.Response(200, text=_SITEMAP_XML)
        return httpx.Response(
            200, text="<html>irrelevant, _parse_product_page is fixed</html>"
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        book = Book(title="Matching Title", author="Some Author")
        editions = await _MatchesButOutOfStockClient().find_editions(book, http_client)

    # ADR 0002: "never carried" and "out of stock" collapse into one
    # "not available" result — an out-of-stock match must look identical to
    # no match at all (empty list), not appear in the list with a null price.
    assert editions == []


@pytest.mark.asyncio
async def test_search_titles_returns_book_even_when_out_of_stock(
    tmp_path, monkeypatch
) -> None:
    # search_titles() is for free-text search discovery, not availability —
    # a Book must be findable even if currently out of stock everywhere
    # (see CONTEXT.md: Availability is a property of an Edition, not a Book).
    from book_finder import config

    monkeypatch.setattr(config.settings, "cache_dir", tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        if "sitemap" in str(request.url):
            return httpx.Response(200, text=_SITEMAP_XML)
        return httpx.Response(
            200, text="<html>irrelevant, _parse_product_page is fixed</html>"
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        books = await _MatchesButOutOfStockClient().search_titles(
            "matching title", http_client
        )

    assert books == [Book(title="Matching Title", author="Some Author")]


@pytest.mark.asyncio
async def test_search_titles_returns_empty_when_nothing_shortlisted(
    tmp_path, monkeypatch
) -> None:
    from book_finder import config

    monkeypatch.setattr(config.settings, "cache_dir", tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_SITEMAP_XML)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        books = await _MatchesButOutOfStockClient().search_titles(
            "nothing like it", http_client
        )

    assert books == []
