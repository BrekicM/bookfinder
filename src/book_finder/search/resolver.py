from dataclasses import dataclass, field
from typing import Literal

from book_finder.domain.models import Book

MAX_CANDIDATES = 10


@dataclass
class SearchResolution:
    kind: Literal["single", "ambiguous", "none"]
    book: Book | None = None
    candidates: list[Book] = field(default_factory=list)


def _book_from_result(result: dict) -> Book | None:
    title = result.get("title")
    if not title:
        return None
    authors = result.get("author_name") or []
    author = authors[0] if authors else ""
    return Book(title=title, author=author)


def resolve(raw_results: list[dict]) -> SearchResolution:
    """Collapse already-fetched search results into one Book, several, or none.

    Fetching is the caller's job: results come from several sources whose
    order matters (store-native results first, so they survive the
    MAX_CANDIDATES truncation), and only the caller knows that order.
    """
    distinct: dict[tuple[str, str], Book] = {}
    for result in raw_results:
        book = _book_from_result(result)
        if book is None:
            continue
        distinct.setdefault(book.identity_key(), book)

    books = list(distinct.values())

    if not books:
        return SearchResolution(kind="none")
    if len(books) == 1:
        return SearchResolution(kind="single", book=books[0])
    return SearchResolution(kind="ambiguous", candidates=books[:MAX_CANDIDATES])
