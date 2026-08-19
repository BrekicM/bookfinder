import httpx
from bs4 import BeautifulSoup

from book_finder.domain.models import Book, Genre, PopularityEntry
from book_finder.popularity.genre_mapping import LAGUNA_GENRE_URLS, VULKAN_GENRE_URLS


def parse_laguna_top_liste(html: str) -> list[PopularityEntry]:
    soup = BeautifulSoup(html, "lxml")
    titles = soup.find_all("h2", class_="line-clamp-2")
    authors = soup.find_all("span", class_="text-[#4B5563]")

    entries = []
    for title_el, author_el in zip(titles, authors, strict=False):
        title = title_el.get_text(strip=True)
        if not title:
            continue
        entries.append(
            PopularityEntry(
                book=Book(title=title, author=author_el.get_text(strip=True)),
                rank=len(entries) + 1,
                source="Laguna Top lista",
            )
        )
    return entries


def parse_vulkan_top_liste(html: str) -> list[PopularityEntry]:
    soup = BeautifulSoup(html, "lxml")
    heading = next(
        (h for h in soup.find_all("h1") if "top lista" in h.get_text(strip=True).casefold()),
        None,
    )
    if heading is None:
        return []

    entries = []
    for title_el in heading.find_all_next("h3", class_="nb-title"):
        # Real books have an author-name link; page footer/nav items reusing
        # the same product-card markup don't, which is what filters them out.
        author_el = title_el.find_next("a", class_="author-name")
        if author_el is None:
            continue
        title = title_el.get_text(strip=True)
        if not title:
            continue
        entries.append(
            PopularityEntry(
                book=Book(title=title, author=author_el.get_text(strip=True)),
                rank=len(entries) + 1,
                source="Vulkan Top lista",
            )
        )
    return entries


def has_serbian_source(genre: Genre) -> bool:
    return genre in LAGUNA_GENRE_URLS or genre in VULKAN_GENRE_URLS


async def fetch_serbian_popularity(
    genre: Genre, http_client: httpx.AsyncClient
) -> list[PopularityEntry]:
    sources = []
    if genre in LAGUNA_GENRE_URLS:
        sources.append((LAGUNA_GENRE_URLS[genre], parse_laguna_top_liste))
    if genre in VULKAN_GENRE_URLS:
        sources.append((VULKAN_GENRE_URLS[genre], parse_vulkan_top_liste))

    combined: list[PopularityEntry] = []
    any_success = False
    for url, parser in sources:
        try:
            response = await http_client.get(url, timeout=8.0)
            response.raise_for_status()
        except httpx.HTTPError:
            continue
        any_success = True
        combined.extend(parser(response.text))

    if sources and not any_success:
        raise httpx.HTTPError(f"All Serbian sources failed for genre {genre.value}")

    return [
        PopularityEntry(book=e.book, rank=i + 1, source=e.source) for i, e in enumerate(combined)
    ]
