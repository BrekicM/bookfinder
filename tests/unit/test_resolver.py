from book_finder.search.resolver import resolve


def test_zero_results_returns_none_kind() -> None:
    resolution = resolve([])
    assert resolution.kind == "none"


def test_single_result_returns_single_kind() -> None:
    results = [{"title": "1984", "author_name": ["George Orwell"]}]
    resolution = resolve(results)

    assert resolution.kind == "single"
    assert resolution.book.title == "1984"
    assert resolution.book.author == "George Orwell"


def test_multiple_editions_of_same_work_collapse_to_single() -> None:
    # Open Library returns one row per edition/language variant of the same
    # work — this must NOT be treated as ambiguous.
    results = [
        {"title": "1984", "author_name": ["George Orwell"]},
        {"title": "1984", "author_name": ["George Orwell"]},
        {"title": "1984", "author_name": ["George Orwell"]},
    ]
    resolution = resolve(results)
    assert resolution.kind == "single"


def test_genuinely_different_works_are_ambiguous() -> None:
    results = [
        {"title": "1984", "author_name": ["George Orwell"]},
        {"title": "1985", "author_name": ["Anthony Burgess"]},
    ]
    resolution = resolve(results)

    assert resolution.kind == "ambiguous"
    titles = {c.title for c in resolution.candidates}
    assert titles == {"1984", "1985"}


def test_same_title_different_authors_is_ambiguous() -> None:
    results = [
        {"title": "Carrie", "author_name": ["Stephen King"]},
        {"title": "Carrie", "author_name": ["Some Other Author"]},
    ]
    resolution = resolve(results)
    assert resolution.kind == "ambiguous"


def test_results_missing_author_are_skipped_not_crashed_on() -> None:
    results = [{"title": "No Author Here"}]
    resolution = resolve(results)

    assert resolution.kind == "single"
    assert resolution.book.author == ""


def test_truncation_keeps_the_earliest_distinct_results() -> None:
    # For an internationally famous title, Open Library alone can return more
    # than MAX_CANDIDATES distinct editions/translations. Whoever the caller
    # puts first in the results list survives truncation — this is why
    # routes_search.py orders Serbian-bookstore results ahead of Open
    # Library's: a purchasable-in-Serbia match must not be crowded out.
    results = [{"title": f"Edition {i}", "author_name": ["Author"]} for i in range(30)]
    resolution = resolve(results)

    assert resolution.kind == "ambiguous"
    titles = [c.title for c in resolution.candidates]
    assert titles == [f"Edition {i}" for i in range(25)]
