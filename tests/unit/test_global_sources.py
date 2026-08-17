from book_finder.domain.models import Genre
from book_finder.popularity.global_sources import GENRE_SUBJECTS, build_entries


def test_build_entries_from_empty_works_list() -> None:
    assert build_entries([]) == []


def test_build_entries_assigns_rank_by_position() -> None:
    works = [{"title": "First Book"}, {"title": "Second Book"}, {"title": "Third Book"}]
    entries = build_entries(works)

    assert [e.rank for e in entries] == [1, 2, 3]
    assert [e.book.title for e in entries] == ["First Book", "Second Book", "Third Book"]
    assert all(e.source == "Open Library" for e in entries)
    assert all(e.book.author == "" for e in entries)


def test_build_entries_skips_works_missing_title() -> None:
    works = [{"title": "Has Title"}, {"no_title": "oops"}, {"title": "Also Has Title"}]
    entries = build_entries(works)

    assert [e.book.title for e in entries] == ["Has Title", "Also Has Title"]
    # rank reflects position in the *output* list, not the raw input
    assert [e.rank for e in entries] == [1, 2]


def test_every_genre_has_an_open_library_subject_mapping() -> None:
    assert set(GENRE_SUBJECTS.keys()) == set(Genre)
