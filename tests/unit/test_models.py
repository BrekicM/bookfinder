from book_finder.domain.models import Availability, Book, Bookstore, Edition, Genre


def test_genre_has_exactly_nine_members() -> None:
    assert len(Genre) == 9


def test_bookstore_has_exactly_five_members() -> None:
    # Delfi added per ADR 0004; Booka added per ADR 0009; Čarobna knjiga added per ADR 0010.
    assert len(Bookstore) == 5


def test_edition_script_defaults_to_none() -> None:
    edition = Edition(
        book=Book(title="1984", author="George Orwell"),
        bookstore=Bookstore.LAGUNA,
        availability=Availability.AVAILABLE,
        language="Serbian",
        url="https://example.com/x",
    )
    assert edition.script is None


def test_edition_script_can_be_set() -> None:
    edition = Edition(
        book=Book(title="1984", author="George Orwell"),
        bookstore=Bookstore.BOOKA,
        availability=Availability.AVAILABLE,
        language="Serbian",
        script="Latin",
        url="https://booka.rs/knjige/x",
    )
    assert edition.script == "Latin"


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
