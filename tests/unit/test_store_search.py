from book_finder.domain.models import Book
from book_finder.search.store_search import books_to_search_dicts

# The per-store search wrappers (search_delfi_books / search_booka_books) and
# editions_to_search_dicts used to live here. Both stores now expose a real
# search_titles() returning list[Book], so the route adapts every client
# uniformly and those wrappers are gone. Their behavior coverage moved to
# test_delfi_client.py / test_booka_client.py.


def test_books_to_search_dicts_empty_list_returns_empty() -> None:
    assert books_to_search_dicts([]) == []


def test_books_to_search_dicts_includes_author() -> None:
    book = Book(title="Leto bez muskaraca", author="Siri Hustvedt")
    assert books_to_search_dicts([book]) == [
        {"title": "Leto bez muskaraca", "author_name": ["Siri Hustvedt"]}
    ]


def test_books_to_search_dicts_omits_author_name_when_author_is_unknown() -> None:
    book = Book(title="No Author Book", author="")
    assert books_to_search_dicts([book]) == [
        {"title": "No Author Book", "author_name": []}
    ]
