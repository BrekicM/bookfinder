import html
import json
from urllib.parse import quote

import httpx

from book_finder.config import settings
from book_finder.domain.models import Availability, Book, Bookstore, Edition

SEARCH_URL = "https://booka.rs/wp-json/wc/store/v1/products?search={query}"
PRODUCT_URL = "https://booka.rs/wp-json/wp/v2/product?slug={slug}"
PISAC_URL = "https://booka.rs/wp-json/wp/v2/pisac/{term_id}"

# Booka's search API mixes books with merch (tote bags, etc.) sharing the same
# catalog. Book product pages live under /knjige/; everything else is not a
# Book/Edition for this app's purposes.
BOOK_PATH_SEGMENT = "/knjige/"

_SCRIPT_LABELS = {"latinica": "Latin", "ćirilica": "Cyrillic", "cirilica": "Cyrillic"}


def build_search_url(query: str) -> str:
    # quote(..., safe="") also encodes "/", matching Delfi's handling of
    # titles containing slashes (omnibus editions).
    return SEARCH_URL.format(query=quote(query, safe=""))


def _attribute_value(item: dict, name: str) -> str | None:
    for attribute in item.get("attributes", []):
        if attribute.get("name") == name:
            terms = attribute.get("terms") or []
            if terms:
                return terms[0].get("name")
    return None


def _script_label(raw: str | None) -> str | None:
    if raw is None:
        return None
    return _SCRIPT_LABELS.get(raw.strip().lower(), raw)


def _price_rsd(prices: dict) -> float | None:
    raw_price = prices.get("price")
    minor_unit = prices.get("currency_minor_unit")
    if raw_price in (None, "") or minor_unit is None:
        return None
    return float(raw_price) / (10**minor_unit)


def parse_search_item(item: dict) -> Edition | None:
    permalink = item.get("permalink")
    name = item.get("name")
    if not permalink or not name or BOOK_PATH_SEGMENT not in permalink:
        return None

    is_available = bool(item.get("is_in_stock", False))
    price = _price_rsd(item.get("prices", {})) if is_available else None

    return Edition(
        book=Book(title=html.unescape(name), author=""),
        bookstore=Bookstore.BOOKA,
        availability=Availability.AVAILABLE if is_available else Availability.NOT_AVAILABLE,
        price_rsd=price,
        # Booka's Store API doesn't expose the edition's language directly,
        # but it's a domestic Serbian retailer selling translated/domestic
        # literature (mirrors Delfi/Vulkan's same default).
        language="Serbian",
        format_label=_attribute_value(item, "Povez"),
        script=_script_label(_attribute_value(item, "Pismo")),
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


