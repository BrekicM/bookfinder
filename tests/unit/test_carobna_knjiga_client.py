import httpx
import pytest

from book_finder.stores import carobna_knjiga as ck_module
from book_finder.stores.carobna_knjiga import CarobnaKnjigaClient


def _genre_page_html(product_urls: list[str], *, next_disabled: bool) -> str:
    cards = "".join(
        f'<div class="block product bg-transparent text-center no-radius">'
        f'<div class="product-image"><a href="{url}"></a></div>'
        f"</div>"
        for url in product_urls
    )
    next_class = "page-item disabled" if next_disabled else "page-item"
    pagination = (
        '<ul class="pagination justify-content-center">'
        f'<li class="{next_class}"><a class="page-link">Sledeća</a></li>'
        "</ul>"
    )
    return f"<html><body>{cards}{pagination}</body></html>"


@pytest.mark.asyncio
async def test_fetch_catalog_urls_returns_products_from_a_single_page_genre(
    monkeypatch,
) -> None:
    monkeypatch.setattr(ck_module, "BOOK_GENRE_SLUGS", ["fantastika"])

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://carobnaknjiga.rs/fantastika/1"
        return httpx.Response(
            200,
            text=_genre_page_html(
                ["https://carobnaknjiga.rs/prah", "https://carobnaknjiga.rs/mali-princ"],
                next_disabled=True,
            ),
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        urls = await CarobnaKnjigaClient()._fetch_catalog_urls(http_client)

    assert urls == ["https://carobnaknjiga.rs/prah", "https://carobnaknjiga.rs/mali-princ"]


@pytest.mark.asyncio
async def test_fetch_catalog_urls_follows_pagination_within_a_genre(monkeypatch) -> None:
    monkeypatch.setattr(ck_module, "BOOK_GENRE_SLUGS", ["fantastika"])

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == "https://carobnaknjiga.rs/fantastika/1":
            return httpx.Response(
                200,
                text=_genre_page_html(["https://carobnaknjiga.rs/prah"], next_disabled=False),
            )
        if url == "https://carobnaknjiga.rs/fantastika/2":
            return httpx.Response(
                200,
                text=_genre_page_html(["https://carobnaknjiga.rs/mali-princ"], next_disabled=True),
            )
        raise AssertionError(f"unexpected request: {url}")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        urls = await CarobnaKnjigaClient()._fetch_catalog_urls(http_client)

    assert urls == ["https://carobnaknjiga.rs/prah", "https://carobnaknjiga.rs/mali-princ"]


@pytest.mark.asyncio
async def test_fetch_catalog_urls_dedupes_across_genres_and_crawls_every_genre(
    monkeypatch,
) -> None:
    monkeypatch.setattr(ck_module, "BOOK_GENRE_SLUGS", ["fantastika", "horor"])

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == "https://carobnaknjiga.rs/fantastika/1":
            return httpx.Response(
                200,
                text=_genre_page_html(
                    ["https://carobnaknjiga.rs/prah", "https://carobnaknjiga.rs/shared-title"],
                    next_disabled=True,
                ),
            )
        if url == "https://carobnaknjiga.rs/horor/1":
            return httpx.Response(
                200,
                text=_genre_page_html(
                    [
                        "https://carobnaknjiga.rs/shared-title",
                        "https://carobnaknjiga.rs/danicki-uzas",
                    ],
                    next_disabled=True,
                ),
            )
        raise AssertionError(f"unexpected request: {url}")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        urls = await CarobnaKnjigaClient()._fetch_catalog_urls(http_client)

    assert urls == [
        "https://carobnaknjiga.rs/prah",
        "https://carobnaknjiga.rs/shared-title",
        "https://carobnaknjiga.rs/danicki-uzas",
    ]
