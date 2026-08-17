import httpx
import pytest

from book_finder.domain.models import Book, Edition
from book_finder.stores.base import BookstoreClient, safe_find_editions


class _AlwaysFailsClient(BookstoreClient):
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
async def test_total_catalog_failure_surfaces_as_error_not_empty_result(tmp_path, monkeypatch) -> None:
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
