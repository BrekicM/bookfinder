import pytest

from book_finder.search.resolver import resolve


def _fake_search(results: list[dict]):
    async def search(query: str) -> list[dict]:
        return results

    return search


@pytest.mark.asyncio
async def test_zero_results_returns_none_kind() -> None:
    resolution = await resolve("nonexistent gibberish query", _fake_search([]))
    assert resolution.kind == "none"


@pytest.mark.asyncio
async def test_single_result_returns_single_kind() -> None:
    results = [{"title": "1984", "author_name": ["George Orwell"]}]
    resolution = await resolve("1984", _fake_search(results))

    assert resolution.kind == "single"
    assert resolution.book.title == "1984"
    assert resolution.book.author == "George Orwell"


@pytest.mark.asyncio
async def test_multiple_editions_of_same_work_collapse_to_single() -> None:
    # Open Library returns one row per edition/language variant of the same
    # work — this must NOT be treated as ambiguous.
    results = [
        {"title": "1984", "author_name": ["George Orwell"]},
        {"title": "1984", "author_name": ["George Orwell"]},
        {"title": "1984", "author_name": ["George Orwell"]},
    ]
    resolution = await resolve("1984", _fake_search(results))
    assert resolution.kind == "single"


@pytest.mark.asyncio
async def test_genuinely_different_works_are_ambiguous() -> None:
    results = [
        {"title": "1984", "author_name": ["George Orwell"]},
        {"title": "1985", "author_name": ["Anthony Burgess"]},
    ]
    resolution = await resolve("198", _fake_search(results))

    assert resolution.kind == "ambiguous"
    titles = {c.title for c in resolution.candidates}
    assert titles == {"1984", "1985"}


@pytest.mark.asyncio
async def test_same_title_different_authors_is_ambiguous() -> None:
    results = [
        {"title": "Carrie", "author_name": ["Stephen King"]},
        {"title": "Carrie", "author_name": ["Some Other Author"]},
    ]
    resolution = await resolve("Carrie", _fake_search(results))
    assert resolution.kind == "ambiguous"


@pytest.mark.asyncio
async def test_results_missing_author_are_skipped_not_crashed_on() -> None:
    results = [{"title": "No Author Here"}]
    resolution = await resolve("no author", _fake_search(results))

    assert resolution.kind == "single"
    assert resolution.book.author == ""
