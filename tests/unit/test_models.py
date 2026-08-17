from book_finder.domain.models import Availability, Book, Bookstore, Genre


def test_genre_has_exactly_nine_members() -> None:
    assert len(Genre) == 9


def test_bookstore_has_exactly_three_members() -> None:
    # Delfi added per ADR 0004 (superseding ADR 0003's headless-browser assumption)
    assert len(Bookstore) == 3


def test_availability_has_exactly_two_states() -> None:
    assert len(Availability) == 2


def test_identity_key_normalizes_case() -> None:
    a = Book(title="1984", author="George Orwell")
    b = Book(title="1984", author="GEORGE ORWELL")
    assert a.identity_key() == b.identity_key()


def test_identity_key_normalizes_surrounding_whitespace() -> None:
    a = Book(title="1984", author="George Orwell")
    b = Book(title="  1984  ", author="  George Orwell  ")
    assert a.identity_key() == b.identity_key()


def test_identity_key_collapses_internal_whitespace() -> None:
    a = Book(title="The Great Gatsby", author="F. Scott Fitzgerald")
    b = Book(title="The   Great Gatsby", author="F. Scott Fitzgerald")
    assert a.identity_key() == b.identity_key()


def test_identity_key_distinguishes_different_books() -> None:
    a = Book(title="1984", author="George Orwell")
    b = Book(title="Animal Farm", author="George Orwell")
    assert a.identity_key() != b.identity_key()
