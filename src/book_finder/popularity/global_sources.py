import httpx

from book_finder.domain.models import Book, Genre, PopularityEntry

GENRE_SUBJECTS: dict[Genre, str] = {
    Genre.FICTION: "fiction",
    Genre.FANTASY: "fantasy",
    Genre.SCI_FI: "science_fiction",
    Genre.MYSTERY_THRILLER: "mystery_and_detective_stories",
    Genre.ROMANCE: "romance",
    Genre.NON_FICTION: "nonfiction",
    Genre.YOUNG_ADULT: "young_adult_fiction",
    Genre.CHILDRENS: "juvenile_fiction",
    Genre.PROGRAMMING_TECH: "programming",
}

RESULTS_PER_GENRE = 20


def build_entries(works: list[dict]) -> list[PopularityEntry]:
    entries = []
    for work in works:
        title = work.get("title")
        if not title:
            continue
        entries.append(
            PopularityEntry(
                book=Book(title=title, author=""),
                rank=len(entries) + 1,
                source="Open Library",
            )
        )
    return entries


async def fetch_global_popularity(genre: Genre, http_client: httpx.AsyncClient) -> list[PopularityEntry]:
    subject = GENRE_SUBJECTS[genre]
    response = await http_client.get(
        f"https://openlibrary.org/subjects/{subject}.json",
        params={"limit": RESULTS_PER_GENRE},
        timeout=8.0,
    )
    response.raise_for_status()
    return build_entries(response.json().get("works", []))
