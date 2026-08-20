import json
from urllib.parse import unquote

import httpx
import pytest

from book_finder.domain.models import Book
from book_finder.stores.delfi import DelfiClient, sanitize_query

_OUT_OF_STOCK_RESPONSE = json.dumps(
    {
        "data": {
            "results": [
                {
                    "oldProductId": 111,
                    "title": "Matching Title",
                    "authors": [{"authorName": "Some Author"}],
                    "isAvailable": False,
                    "priceList": {"regularDiscountPrice": 1500},
                    "cover": "Mek",
                }
            ]
        }
    }
)


@pytest.mark.asyncio
async def test_find_editions_excludes_matched_but_out_of_stock_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_OUT_OF_STOCK_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        book = Book(title="Matching Title", author="Some Author")
        editions = await DelfiClient().find_editions(book, http_client)

    # Same ADR 0002 rule as Laguna/Vulkan: an out-of-stock match must look
    # identical to no match at all, not surface with a null price.
    assert editions == []


@pytest.mark.asyncio
async def test_search_titles_returns_book_even_when_out_of_stock() -> None:
    # search_titles() is discovery, not an availability check — a Book stays
    # findable when out of stock, unlike find_editions() (ADR 0002).
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_OUT_OF_STOCK_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        books = await DelfiClient().search_titles("Matching Title", http_client)

    assert books == [Book(title="Matching Title", author="Some Author")]


_UNRELATED_RESPONSE = json.dumps(
    {
        "data": {
            "results": [
                {
                    "oldProductId": 2,
                    "title": "The Facts of Destruction",
                    "authors": [{"authorName": "Rostislav Kocourek"}],
                    "isAvailable": True,
                    "priceList": {"regularDiscountPrice": 1000},
                    "cover": "Mek",
                }
            ]
        }
    }
)


@pytest.mark.asyncio
async def test_search_titles_excludes_titles_unrelated_to_the_query() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_UNRELATED_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        books = await DelfiClient().search_titles("Malo zivota", http_client)

    assert books == []


_AUTHOR_QUERY_RESPONSE = json.dumps(
    {
        "data": {
            "results": [
                {
                    "oldProductId": 3,
                    "title": "21 zlatna poluga",
                    "authors": [{"authorName": "Nenad Gugl"}],
                    "isAvailable": True,
                    "priceList": {"regularDiscountPrice": 1200},
                    "cover": "Mek",
                }
            ]
        }
    }
)


@pytest.mark.asyncio
async def test_search_titles_finds_a_book_by_author_query_with_no_title_overlap() -> None:
    # Delfi's own search API correctly matches by author; the app's
    # relevance filter must not throw that hit away just because the query
    # text isn't in the title.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_AUTHOR_QUERY_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        books = await DelfiClient().search_titles("Nenad Gugl", http_client)

    assert books == [Book(title="21 zlatna poluga", author="Nenad Gugl")]


_KNJIGA_RESPONSE = json.dumps(
    {
        "data": {
            "results": [
                {
                    "oldProductId": 1,
                    "title": "Hobit",
                    "authors": [{"authorName": "Dzon Ronald Rejel Tolkin"}],
                    "isAvailable": True,
                    "priceList": {"regularDiscountPrice": 1000},
                    "cover": "Mek",
                }
            ]
        }
    }
)
_EMPTY_RESPONSE = json.dumps({"data": {"results": []}})


@pytest.mark.asyncio
async def test_find_editions_searches_the_book_categories_not_all_categories() -> None:
    # The unscoped "Sve kategorije" search is capped and can be crowded out
    # entirely by merchandise (mugs, stickers...) for a heavily-merchandised
    # franchise, hiding real books. find_editions() must search the two book
    # categories specifically, not the all-categories endpoint.
    def handler(request: httpx.Request) -> httpx.Response:
        if "/Knjiga/" in str(request.url):
            return httpx.Response(200, text=_KNJIGA_RESPONSE)
        return httpx.Response(200, text=_EMPTY_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        book = Book(title="Hobit", author="Dzon Ronald Rejel Tolkin")
        editions = await DelfiClient().find_editions(book, http_client)

    assert len(editions) == 1
    assert editions[0].book.title == "Hobit"


@pytest.mark.asyncio
async def test_find_editions_dedupes_the_same_product_found_in_both_categories() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_KNJIGA_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        book = Book(title="Hobit", author="Dzon Ronald Rejel Tolkin")
        editions = await DelfiClient().find_editions(book, http_client)

    assert len(editions) == 1


@pytest.mark.asyncio
async def test_find_editions_strips_query_syntax_characters_from_the_search_term() -> None:
    # Delfi's search backend parses the query as Lucene-style query syntax and
    # answers 500 when that syntax is invalid, so a real Open Library title
    # carrying an unbalanced "(" turned every Delfi check into "check failed".
    # The title is only ever matched locally afterwards, so the punctuation is
    # dropped before it reaches the endpoint.
    requested_queries: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_queries.append(unquote(str(request.url).rsplit("/", 1)[-1]))
        return httpx.Response(200, text=_EMPTY_RESPONSE)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        book = Book(title="Mona Lisa Overdrive (The Neuromancer Trilogy", author="William Gibson")
        await DelfiClient().find_editions(book, http_client)

    assert requested_queries == ["Mona Lisa Overdrive The Neuromancer Trilogy"] * 2


def test_sanitize_query_drops_an_operator_left_dangling_at_the_end() -> None:
    # "-", "+", "!" and ":" are operators that bind to the term after them,
    # so Delfi answers 500 on a query ending in a bare operator token.
    assert sanitize_query("Hobit -") == "Hobit"


def test_sanitize_query_drops_a_bare_operator_token_mid_query() -> None:
    # Mid-query a bare operator token doesn't 500 — it silently negates, so
    # Delfi answers 200 with the book missing from the results ("Hobit - -
    # ilustrovano izdanje" loses the book that "Hobit ilustrovano izdanje"
    # finds). That would surface as a false "Not available" rather than a
    # failed check, so the token goes wherever it sits. It carries no
    # searchable text, so dropping it costs no recall.
    assert sanitize_query("Hobit - ilustrovano izdanje") == "Hobit ilustrovano izdanje"
    assert sanitize_query("Hobit - - ilustrovano izdanje") == "Hobit ilustrovano izdanje"


def test_sanitize_query_drops_an_operator_prefixed_to_a_word() -> None:
    # A prefixed operator is the one that really negates: "Hobit
    # -ilustrovano izdanje" and "-Hobit ilustrovano izdanje" both answer 200
    # with the book excluded.
    assert sanitize_query("Hobit -ilustrovano izdanje") == "Hobit ilustrovano izdanje"
    assert sanitize_query("-Hobit ilustrovano izdanje") == "Hobit ilustrovano izdanje"


def test_sanitize_query_is_empty_when_only_operator_tokens_remain() -> None:
    # Nothing searchable is left, so the caller skips the request entirely
    # rather than sending a path segment the endpoint answers 404 for.
    assert sanitize_query("++") == ""


def test_sanitize_query_keeps_a_trailing_dash_or_plus_attached_to_a_word() -> None:
    # Word-attached "-" and "+" return 200 from Delfi with the book still in
    # the results, and stripping them costs real hits: "C++" finds 15
    # products, "C" finds none.
    assert sanitize_query("C++") == "C++"
    assert sanitize_query("Hobit-") == "Hobit-"
    assert sanitize_query("Programiranje u C++") == "Programiranje u C++"


def test_sanitize_query_drops_a_word_final_colon_or_bang_anywhere() -> None:
    # Unlike "-" and "+", a word-final "!" negates the term after it even
    # mid-query ("Hobit! ilustrovano izdanje" answers 200 with the book
    # excluded), and at the end of the query it is a 500. Titles ending in
    # "!" are common in Serbian, so this is broadly reachable.
    assert sanitize_query("Hobit! ilustrovano izdanje") == "Hobit ilustrovano izdanje"
    assert sanitize_query("Ne odustaj!") == "Ne odustaj"
    assert sanitize_query("Upozorenje:") == "Upozorenje"


def test_sanitize_query_drops_the_boost_operator_anywhere_in_the_query() -> None:
    # Unlike the other operators, "^" is a parse error mid-query as well
    # (it wants a term before and a number after), so it goes entirely.
    assert sanitize_query("Hobit ^ ilustrovano") == "Hobit ilustrovano"


def test_sanitize_query_keeps_punctuation_inside_a_word() -> None:
    # Over-stripping costs real hits: Delfi finds "Jean-Paul Sartre" but
    # returns nothing for "Jean Paul Sartre".
    assert sanitize_query("Jean-Paul Sartre") == "Jean-Paul Sartre"


@pytest.mark.asyncio
async def test_find_editions_skips_the_request_when_nothing_searchable_is_left() -> None:
    # An empty query segment is a 404 from the endpoint, which would surface
    # as "check failed" — but there is nothing to check, so it is no match.
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"should not have been requested: {request.url}")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        editions = await DelfiClient().find_editions(Book(title="( )", author=""), http_client)

    assert editions == []
