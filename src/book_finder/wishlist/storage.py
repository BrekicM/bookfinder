import json
import os
from pathlib import Path

from book_finder.domain.models import Book


def list_books(path: Path) -> list[Book]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Book(**entry) for entry in raw]


def _write(path: Path, books: list[Book]) -> None:
    """Replace the wishlist file atomically.

    The wishlist is user data with no upstream to refetch from, so it is never
    truncated in place: the new contents go to a temp file in the same
    directory (same filesystem, so the rename is atomic) and only then replace
    the target. A crash or full disk leaves the previous wishlist intact.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(json.dumps([b.model_dump() for b in books]), encoding="utf-8")
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def add_book(path: Path, book: Book) -> None:
    books = list_books(path)
    if book.identity_key() in {b.identity_key() for b in books}:
        return
    books.append(book)
    _write(path, books)


def remove_book(path: Path, book: Book) -> None:
    books = [b for b in list_books(path) if b.identity_key() != book.identity_key()]
    _write(path, books)


def is_in_wishlist(path: Path, book: Book) -> bool:
    return book.identity_key() in {b.identity_key() for b in list_books(path)}
