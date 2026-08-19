from book_finder.domain.models import Book
from book_finder.stores.base import matches_book, matches_query, shortlist_candidates


def test_no_match_against_blank_candidate_title() -> None:
    book = Book(title="1984", author="George Orwell")
    assert matches_book(candidate_title="", candidate_author="", book=book) is False


def test_matches_exact_title_and_author() -> None:
    book = Book(title="Kosingas 2: Bezdanj", author="Aleksandar Tešić")
    assert matches_book(
        candidate_title="Kosingas 2: Bezdanj",
        candidate_author="Aleksandar Tešić",
        book=book,
    )


def test_matches_case_insensitively() -> None:
    book = Book(title="Kosingas 2: Bezdanj", author="Aleksandar Tešić")
    assert matches_book(
        candidate_title="KOSINGAS 2: BEZDANJ",
        candidate_author="aleksandar tešić",
        book=book,
    )


def test_does_not_match_different_title() -> None:
    book = Book(title="1984", author="George Orwell")
    assert (
        matches_book(candidate_title="Animal Farm", candidate_author="George Orwell", book=book)
        is False
    )


def test_does_not_match_different_author_surname() -> None:
    book = Book(title="1984", author="George Orwell")
    assert matches_book(candidate_title="1984", candidate_author="Jack London", book=book) is False


def test_matches_when_query_author_lacks_diacritics_store_has_them() -> None:
    # A real user typing on an English keyboard won't type "Tešić" — this is
    # the exact case that silently produced false "Not available" results
    # when driving the app manually against the live Laguna site.
    book = Book(title="Kosingas 2: Bezdanj", author="Aleksandar Tesic")
    assert matches_book(
        candidate_title="Kosingas 2: Bezdanj",
        candidate_author="Aleksandar Tešić",
        book=book,
    )


def test_matches_when_candidate_author_is_unknown() -> None:
    book = Book(title="1984", author="George Orwell")
    assert matches_book(candidate_title="1984", candidate_author="", book=book)


def test_matches_when_candidate_title_has_extra_marketing_text() -> None:
    book = Book(title="Urgum Sekiraš", author="Kjartan Poskit")
    assert matches_book(
        candidate_title="Laguna - Urgum Sekiraš - Kjartan Poskit - Knjige o kojima se priča",
        candidate_author="Kjartan Poskit",
        book=book,
    )


def test_query_matches_candidate_title_ignoring_author() -> None:
    # Search discovery has no author to check against — only the free-text query.
    assert matches_query(candidate_title="1984 - George Orwell", query="1984")


def test_query_does_not_match_unrelated_candidate_title() -> None:
    # Store search APIs do their own fuzzy ranking and return hits with no
    # textual overlap with the query; those must be filtered out.
    assert matches_query(candidate_title="Animal Farm", query="1984") is False


def test_query_matches_candidate_title_without_diacritics() -> None:
    assert matches_query(candidate_title="Urgum Sekiraš", query="urgum sekiras")


def test_blank_query_matches_nothing() -> None:
    assert matches_query(candidate_title="1984", query="") is False


def test_query_matches_candidate_author_when_title_does_not_overlap() -> None:
    # A free-text search can legitimately be an author's name, not a title
    # fragment — the store's own search API matches it correctly, and this
    # filter must not throw that hit away.
    assert matches_query(
        candidate_title="21 zlatna poluga", query="Nenad Gugl", candidate_author="Nenad Gugl"
    )


def test_query_matches_candidate_author_surname_only() -> None:
    assert matches_query(
        candidate_title="21 zlatna poluga", query="Gugl", candidate_author="Nenad Gugl"
    )


def test_query_still_rejects_candidate_matching_neither_title_nor_author() -> None:
    assert (
        matches_query(candidate_title="Animal Farm", query="1984", candidate_author="George Orwell")
        is False
    )


CATALOG = [
    "https://laguna.rs/proizvodi/knjige/urgum-sekiras/",
    "https://laguna.rs/proizvodi/knjige/mesecev-tigar/",
    "https://laguna.rs/proizvodi/gift/mini-igracka-kuca-misica-sem-i-julija-klompe/",
    "https://www.knjizare-vulkan.rs/roman/311296-staza-paukovih-gnezda",
]


def test_shortlist_finds_matching_laguna_url() -> None:
    book = Book(title="Urgum Sekiraš", author="Kjartan Poskit")
    assert shortlist_candidates(book, CATALOG) == [
        "https://laguna.rs/proizvodi/knjige/urgum-sekiras/"
    ]


def test_shortlist_finds_matching_vulkan_url_despite_numeric_id_prefix() -> None:
    book = Book(title="Staza paukovih gnezda", author="Italo Kalvino")
    assert shortlist_candidates(book, CATALOG) == [
        "https://www.knjizare-vulkan.rs/roman/311296-staza-paukovih-gnezda"
    ]


def test_shortlist_returns_empty_when_nothing_matches() -> None:
    book = Book(title="Nonexistent Title Entirely", author="Nobody")
    assert shortlist_candidates(book, CATALOG) == []
