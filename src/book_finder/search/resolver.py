from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Literal

from book_finder.domain.models import Book

MAX_CANDIDATES = 10

SearchFn = Callable[[str], Awaitable[list[dict]]]


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


async def resolve(query: str, search: SearchFn) -> SearchResolution:
    raw_results = await search(query)

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
