from book_finder.domain.models import Book
from book_finder.wishlist.storage import (
    add_book,
    is_in_wishlist,
    list_books,
    remove_book,
)


def test_list_books_returns_empty_when_file_missing(tmp_path) -> None:
    assert list_books(tmp_path / "wishlist.json") == []


def test_add_book_then_list_returns_it(tmp_path) -> None:
    path = tmp_path / "wishlist.json"
    add_book(path, Book(title="1984", author="George Orwell"))

    assert list_books(path) == [Book(title="1984", author="George Orwell")]


def test_add_same_book_twice_does_not_duplicate(tmp_path) -> None:
    path = tmp_path / "wishlist.json"
    add_book(path, Book(title="1984", author="George Orwell"))
    add_book(path, Book(title="1984", author="George Orwell"))

    assert list_books(path) == [Book(title="1984", author="George Orwell")]


def test_add_book_identity_key_dedup_ignores_case_and_whitespace(tmp_path) -> None:
    path = tmp_path / "wishlist.json"
    add_book(path, Book(title="1984", author="George Orwell"))
    add_book(path, Book(title="  1984  ", author="GEORGE ORWELL"))

    assert list_books(path) == [Book(title="1984", author="George Orwell")]


def test_remove_book_removes_it_from_the_list(tmp_path) -> None:
    path = tmp_path / "wishlist.json"
    add_book(path, Book(title="1984", author="George Orwell"))
    add_book(path, Book(title="Brave New World", author="Aldous Huxley"))

    remove_book(path, Book(title="1984", author="George Orwell"))

    assert list_books(path) == [Book(title="Brave New World", author="Aldous Huxley")]


def test_remove_book_when_missing_is_a_no_op(tmp_path) -> None:
    path = tmp_path / "wishlist.json"

    remove_book(path, Book(title="1984", author="George Orwell"))

    assert list_books(path) == []


def test_is_in_wishlist_false_when_not_added(tmp_path) -> None:
    path = tmp_path / "wishlist.json"

    assert is_in_wishlist(path, Book(title="1984", author="George Orwell")) is False


def test_is_in_wishlist_true_after_add(tmp_path) -> None:
    path = tmp_path / "wishlist.json"
    add_book(path, Book(title="1984", author="George Orwell"))

    assert is_in_wishlist(path, Book(title="1984", author="George Orwell")) is True
