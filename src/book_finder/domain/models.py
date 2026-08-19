import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel


def _normalize_for_identity(text: str) -> str:
    """Collapse whitespace and case only — deliberately NOT diacritic-folding.

    Book identity (wishlist membership, dedup) must keep š/č/ć/ž/đ significant:
    two Books whose titles differ only by diacritics are still two Books. The
    lossier fold used to match a Book against a Bookstore's own text lives in
    stores/base.py as _normalize_for_matching.
    """
    return re.sub(r"\s+", " ", text).strip().casefold()


class Genre(str, Enum):
    """The fixed, curated set of genres. See CONTEXT.md — closed membership, not derived from any source's taxonomy."""

    FICTION = "Fiction"
    FANTASY = "Fantasy"
    SCI_FI = "Sci-Fi"
    MYSTERY_THRILLER = "Mystery/Thriller"
    ROMANCE = "Romance"
    NON_FICTION = "Non-Fiction"
    YOUNG_ADULT = "Young Adult"
    CHILDRENS = "Children's"
    PROGRAMMING_TECH = "Programming/Tech"


class Bookstore(str, Enum):
    """The Serbian retailers the app checks. See ADR 0004 for Delfi's late addition."""

    LAGUNA = "Laguna"
    VULKAN = "Vulkan"
    DELFI = "Delfi"
    BOOKA = "Booka"


class Availability(str, Enum):
    """Exactly two states per ADR 0002: 'not carried' and 'out of stock' are deliberately collapsed."""

    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"


class Book(BaseModel):
    """A literary work identified by title and author. See CONTEXT.md — not an Edition."""

    title: str
    author: str

    def identity_key(self) -> tuple[str, str]:
        return (_normalize_for_identity(self.title), _normalize_for_identity(self.author))


class Edition(BaseModel):
    """One Bookstore's specific listing of a Book: its own price, language, and stock status."""

    book: Book
    bookstore: Bookstore
    availability: Availability
    price_rsd: float | None = None
    language: str
    format_label: str | None = None
    script: str | None = None
    url: str


class PopularityEntry(BaseModel):
    book: Book
    rank: int
    source: str


class PopularityList(BaseModel):
    genre: Genre
    scope: Literal["global", "serbian"]
    entries: list[PopularityEntry]
    available: bool
