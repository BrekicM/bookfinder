import html
import json
import re
from urllib.parse import quote

import httpx

from book_finder.config import settings
from book_finder.domain.models import Availability, Book, Bookstore, Edition
from book_finder.stores.base import BookstoreClient, matches_book, matches_query

SEARCH_URL = "https://agoraknjige.rs/wp-json/wc/store/v1/products?search={query}"

# Agora exposes no structured author field anywhere (not in the API, not on
# the product page HTML) — every sampled title (10/10) follows a strict
# "Author: Title" colon convention instead, so the title itself is the only
# author source. See ADR 0012.
_SCRIPT_LABELS = {"latinica": "Latin", "ćirilica": "Cyrillic", "cirilica": "Cyrillic"}
_LANGUAGE_LABELS = {"srpski": "Serbian", "engleski": "English"}

# short_description key:value fragments, used to bound a lazily-captured
# label's value when the next label immediately follows with no separator
# (real samples mix ";"-separated and bare-space-separated fragments).
_KNOWN_LABELS = [
    "Izdavač",
    "Godina izdanja",
    "Jezik",
    "Pismo",
    "Povez",
    "Žanr knjige",
    "ISBN broj",
    "Broj strana",
    "Format",
]

# Only one bundle listing is known to exist today (a book + audio CD) — this
# is a small, targeted suffix check, not a general bundle parser. See ADR 0012.
_BUNDLE_SUFFIX = " + ZVUČNA KNJIGA NA CD-U"
_BUNDLE_FORMAT_LABEL = "Zvučna knjiga (CD)"


def build_search_url(query: str) -> str:
    # quote(..., safe="") also encodes "/", matching Booka/Delfi's handling
    # of titles containing slashes (omnibus editions).
    return SEARCH_URL.format(query=quote(query, safe=""))


def _extract_label(short_description: str, label: str) -> str | None:
    """Pull a "Label: value" fragment out of Agora's short_description text.

    Separators are inconsistent across products (";"-separated in some,
    bare-space-separated in others), so this can't be a rigid split — it
    captures lazily up to the next ";", the next known label word, or the
    end of the string.
    """
    if not short_description:
        return None

    other_labels = "|".join(re.escape(l) for l in _KNOWN_LABELS if l != label)
    pattern = rf"{re.escape(label)}\s*:\s*(.+?)(?:;|\s+(?:{other_labels})\s*:|$)"
    match = re.search(pattern, short_description)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def _script_label(short_description: str) -> str | None:
    raw = _extract_label(short_description, "Pismo")
    if raw is None:
        return None
    return _SCRIPT_LABELS.get(raw.strip().lower(), raw)


def _language_label(short_description: str) -> str:
    # Domestic Serbian retailer selling translated/domestic literature
    # (mirrors Delfi/Vulkan/Booka's same default) — but Agora's field is
    # usually present, so prefer parsing it over blindly defaulting.
    raw = _extract_label(short_description, "Jezik")
    if raw is None:
        return "Serbian"
    return _LANGUAGE_LABELS.get(raw.strip().lower(), "Serbian")


def _format_label(short_description: str) -> str | None:
    return _extract_label(short_description, "Povez")


def _split_author_title(raw_name: str) -> tuple[str, str, bool]:
    """Split "Author: Title" on the FIRST colon; detect a trailing bundle suffix first.

    A title with no colon is not skipped — it's an unresolved-author edition
    (author "", full raw string as title), which matches_book's
    fallback-to-title-only-when-empty-author handles directly.
    """
    is_bundle = raw_name.endswith(_BUNDLE_SUFFIX)
    name = raw_name[: -len(_BUNDLE_SUFFIX)] if is_bundle else raw_name

    if ":" in name:
        author, _, title = name.partition(":")
        return author.strip(), title.strip(), is_bundle
    return "", name.strip(), is_bundle


def _price_rsd(prices: dict) -> float | None:
    raw_price = prices.get("price")
    minor_unit = prices.get("currency_minor_unit")
    if raw_price in (None, "") or minor_unit is None:
        return None
    return float(raw_price) / (10**minor_unit)


def parse_search_item(item: dict) -> Edition | None:
    permalink = item.get("permalink")
    name = item.get("name")
    if not permalink or not name:
        return None

    author, title, is_bundle = _split_author_title(html.unescape(name))
    short_description = item.get("short_description") or ""

    is_available = bool(item.get("is_in_stock", False))
    price = _price_rsd(item.get("prices", {})) if is_available else None

    format_label = _BUNDLE_FORMAT_LABEL if is_bundle else _format_label(short_description)

    return Edition(
        book=Book(title=title, author=author),
        bookstore=Bookstore.AGORA,
        availability=Availability.AVAILABLE if is_available else Availability.NOT_AVAILABLE,
        price_rsd=price,
        language=_language_label(short_description),
        format_label=format_label,
        script=_script_label(short_description),
        url=permalink,
    )


def parse_search_results(raw_json: str) -> list[Edition]:
    data = json.loads(raw_json)
    editions = []
    for item in data:
        edition = parse_search_item(item)
        if edition is not None:
            editions.append(edition)
    return editions


async def fetch_search_results(query: str, http_client: httpx.AsyncClient) -> list[Edition]:
    response = await http_client.get(
        build_search_url(query), timeout=settings.store_request_timeout_seconds
    )
    response.raise_for_status()
    return parse_search_results(response.text)


class AgoraClient(BookstoreClient):
    """Agora exposes the same WooCommerce Store API search endpoint as Booka
    (ADR 0009), used directly rather than the sitemap-and-shortlist base. See
    ADR 0012. Unlike Booka, author is never a second HTTP round trip — it's
    parsed straight out of the "Author: Title" search-result title.
    """

    bookstore = Bookstore.AGORA.value

    async def search_titles(self, query: str, http_client: httpx.AsyncClient) -> list[Book]:
        """Free-text search discovery via Agora's own search API.

        Unlike find_editions(), results are not filtered by Availability — a
        Book stays discoverable via search even when out of stock (ADR 0002).
        """
        candidates = await fetch_search_results(query, http_client)
        return [
            edition.book
            for edition in candidates
            if matches_query(
                candidate_title=edition.book.title,
                query=query,
                candidate_author=edition.book.author,
            )
        ]

    async def find_editions(self, book: Book, http_client: httpx.AsyncClient) -> list[Edition]:
        candidates = await fetch_search_results(book.title, http_client)

        return [
            edition
            for edition in candidates
            if edition.availability == Availability.AVAILABLE
            and matches_book(
                candidate_title=edition.book.title,
                candidate_author=edition.book.author,
                book=book,
            )
        ]
