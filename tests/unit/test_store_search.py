from book_finder.domain.models import Availability, Book, Bookstore, Edition
from book_finder.search.store_search import editions_to_search_dicts


def test_empty_list_returns_empty() -> None:
    assert editions_to_search_dicts([]) == []


def test_edition_becomes_a_search_dict_with_author() -> None:
    edition = Edition(
        book=Book(title="Bitka na Sutjesci: Pakao u raju", author="Simun Cimerman"),
        bookstore=Bookstore.DELFI,
        availability=Availability.AVAILABLE,
        price_rsd=1500,
        language="Serbian",
        url="https://delfi.rs/knjige/246557-x.html",
    )

    assert editions_to_search_dicts([edition]) == [
        {"title": "Bitka na Sutjesci: Pakao u raju", "author_name": ["Simun Cimerman"]}
    ]


def test_edition_with_no_author_omits_author_name() -> None:
    edition = Edition(
        book=Book(title="No Author Book", author=""),
        bookstore=Bookstore.DELFI,
        availability=Availability.NOT_AVAILABLE,
        language="Serbian",
        url="https://delfi.rs/knjige/y.html",
    )

    assert editions_to_search_dicts([edition]) == [{"title": "No Author Book", "author_name": []}]
