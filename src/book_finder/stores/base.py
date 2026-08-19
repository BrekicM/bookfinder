import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Literal

import httpx

from book_finder.config import settings
from book_finder.domain.models import Availability, Book, Edition
from book_finder.popularity.cache import read_cache, read_stale, write_cache
from book_finder.stores.sitemap import parse_sitemap_urls
from book_finder.stores.slugify import slugify

# Kept in step with resolver.MAX_CANDIDATES so Laguna/Vulkan aren't a silent
# bottleneck relative to stores with a real search API. Since these two have
# no live search endpoint (see CatalogBookstoreClient docstring), each
# shortlisted candidate costs one live product-page fetch — raising this
# trades search latency for completeness.
MAX_CANDIDATES_TO_FETCH = 25


def _normalize_for_matching(text: str) -> str:
    """Normalize whitespace/case AND fold diacritics, for matching only.

    A title/author typed without Serbian diacritics (very common — most
    keyboards don't have š/č/ć/ž/đ) must still match the store's own
    diacritic-correct text. This fold is deliberately lossier than
    Book.identity_key's _normalize_for_identity, which keeps diacritics
    significant because they distinguish one Book from another.
    """
    folded = slugify(text).replace("-", " ")
    return re.sub(r"\s+", " ", folded).strip()


def matches_book(*, candidate_title: str, candidate_author: str, book: Book) -> bool:
    candidate_title_norm = _normalize_for_matching(candidate_title)
    book_title_norm = _normalize_for_matching(book.title)

    if not candidate_title_norm or not book_title_norm:
        return False
    if book_title_norm not in candidate_title_norm:
        return False

    if not candidate_author.strip():
        return True

    surname = _normalize_for_matching(book.author).split(" ")[-1]
    return surname in _normalize_for_matching(candidate_author)


def matches_query(*, candidate_title: str, query: str, candidate_author: str = "") -> bool:
    """Is a search-discovery candidate relevant to the free-text query?

    Relevant if the query text overlaps the candidate's title OR its author
    (when known) — the query might be a title fragment or an author's name,
    and store search APIs (plus Open Library) do their own fuzzy ranking
    that surfaces hits with no textual overlap with either.

    Not a substitute for matches_book(..., candidate_author="") inside
    find_editions(), where an empty candidate author means "author not
    resolved yet" and must still be re-checked before a result is kept.
    """
    query_norm = _normalize_for_matching(query)
    if not query_norm:
        return False

    title_norm = _normalize_for_matching(candidate_title)
    if title_norm and query_norm in title_norm:
        return True

    author_norm = _normalize_for_matching(candidate_author)
    return bool(author_norm) and query_norm in author_norm


def url_slug(url: str) -> str:
    """The trailing path segment of a product URL, ignoring any trailing slash."""
    return url.rstrip("/").rsplit("/", 1)[-1]


def shortlist_candidates(book: Book, catalog_urls: list[str]) -> list[str]:
    """Match a Book's title against a cached catalog of store URLs, without fetching anything.

    Store URL slugs are diacritic-stripped and sometimes numeric-ID-prefixed
    (Vulkan), so comparison happens in slug space, not on raw candidate pages.
    """
    title_slug = slugify(book.title)
    return [url for url in catalog_urls if title_slug in slugify(url_slug(url))]


class BookstoreClient(ABC):
    """Checks one Bookstore for Editions of a Book.

    The narrow contract every Bookstore satisfies, however it talks to its
    store: a live Availability check (find_editions) and free-text discovery
    (search_titles). Stores with a real search API (Delfi, Booka) implement
    both directly; stores without one (Laguna, Vulkan) inherit the
    sitemap-catalog implementations from CatalogBookstoreClient.
    """

    bookstore: str

    @abstractmethod
    async def find_editions(self, book: Book, http_client: httpx.AsyncClient) -> list[Edition]:
        """Editions of this Book currently in stock at this Bookstore.

        Filtered to Availability.AVAILABLE — per ADR 0002, a matched-but-out-
        of-stock Edition must look identical to no match at all.
        """
        ...

    @abstractmethod
    async def search_titles(self, query: str, http_client: httpx.AsyncClient) -> list[Book]:
        """Free-text search discovery against this Bookstore.

        Deliberately NOT filtered by Availability (unlike find_editions) — a
        Book stays discoverable by search even when currently out of stock;
        only the /books live-check page cares about stock status.
        """
        ...


class CatalogBookstoreClient(BookstoreClient):
    """A Bookstore with no usable live search endpoint, served from a sitemap catalog.

    Neither Laguna nor Vulkan exposes a working live search endpoint (confirmed
    during implementation: Laguna's search box is client-side JS only, Vulkan's
    search is an undocumented AJAX endpoint). find_editions() instead matches
    against a cached, sitemap-derived catalog of that store's product URLs, then
    fetches and parses only the shortlisted candidates live. The catalog itself
    changes rarely and is cached like popularity data; the actual Availability/
    price check on the shortlisted pages is always live, per ADR 0001.
    """

    sitemap_url: str
    cache_key: str

    def _is_book_url(self, url: str) -> bool:
        return True

    @abstractmethod
    def _parse_product_page(self, html: str) -> Edition | None: ...

    async def _get_catalog(self, http_client: httpx.AsyncClient) -> list[str]:
        max_age = timedelta(hours=settings.catalog_cache_ttl_hours)
        cached = read_cache(settings.cache_dir, self.cache_key, max_age=max_age)
        if cached is not None:
            return cached

        try:
            response = await http_client.get(
                self.sitemap_url, timeout=settings.store_request_timeout_seconds
            )
            response.raise_for_status()
        except httpx.HTTPError:
            # Degrade gracefully only if we have something to degrade to — a
            # total failure with no stale fallback must propagate, or the
            # caller can't tell "genuinely not available" from "couldn't check".
            stale = read_stale(settings.cache_dir, self.cache_key)
            if stale is not None:
                return stale
            raise

        urls = [url for url in parse_sitemap_urls(response.text) if self._is_book_url(url)]
        write_cache(settings.cache_dir, self.cache_key, urls)
        return urls

    async def find_editions(self, book: Book, http_client: httpx.AsyncClient) -> list[Edition]:
        catalog = await self._get_catalog(http_client)
        candidates = shortlist_candidates(book, catalog)[:MAX_CANDIDATES_TO_FETCH]

        editions = []
        for url in candidates:
            try:
                response = await http_client.get(
                    url, timeout=settings.store_request_timeout_seconds
                )
                response.raise_for_status()
            except httpx.HTTPError:
                continue

            edition = self._parse_product_page(response.text)
            if edition is None:
                continue
            if edition.availability != Availability.AVAILABLE:
                # ADR 0002: a matched-but-out-of-stock Edition must look
                # identical to no match at all, not surface with a null price.
                continue
            if matches_book(
                candidate_title=edition.book.title,
                candidate_author=edition.book.author,
                book=book,
            ):
                editions.append(edition)

        return editions

    async def search_titles(self, query: str, http_client: httpx.AsyncClient) -> list[Book]:
        """Free-text search discovery against this store's cached catalog.

        Unlike find_editions(), results are not filtered by Availability — a
        Book is discoverable by search even when currently out of stock
        everywhere; only the /books live-check page cares about stock status.
        """
        catalog = await self._get_catalog(http_client)
        candidates = shortlist_candidates(Book(title=query, author=""), catalog)[
            :MAX_CANDIDATES_TO_FETCH
        ]

        books = []
        for url in candidates:
            try:
                response = await http_client.get(
                    url, timeout=settings.store_request_timeout_seconds
                )
                response.raise_for_status()
            except httpx.HTTPError:
                continue

            edition = self._parse_product_page(response.text)
            if edition is not None:
                books.append(edition.book)

        return books


@dataclass
class StoreCheckResult:
    bookstore: str
    status: Literal["ok", "timeout", "error"]
    editions: list[Edition] = field(default_factory=list)
    error_message: str | None = None


async def safe_find_editions(
    client: BookstoreClient, book: Book, http_client: httpx.AsyncClient
) -> StoreCheckResult:
    """find_editions() wrapped so one store's failure never blocks the others."""
    try:
        editions = await client.find_editions(book, http_client)
        return StoreCheckResult(bookstore=client.bookstore, status="ok", editions=editions)
    except httpx.TimeoutException as exc:
        return StoreCheckResult(
            bookstore=client.bookstore, status="timeout", error_message=str(exc)
        )
    except httpx.HTTPError as exc:
        return StoreCheckResult(bookstore=client.bookstore, status="error", error_message=str(exc))
