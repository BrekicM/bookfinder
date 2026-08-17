from pathlib import Path

from book_finder.popularity.serbian_sources import parse_laguna_top_liste

FIXTURES = Path(__file__).parent / "fixtures"


def test_returns_empty_list_for_page_with_no_entries() -> None:
    assert parse_laguna_top_liste("<html><body>nothing here</body></html>") == []


def test_parses_real_top_liste_page() -> None:
    html = (FIXTURES / "laguna_top_liste_beletristika.html").read_text(encoding="utf-8")
    entries = parse_laguna_top_liste(html)

    assert len(entries) == 40
    assert entries[0].rank == 1
    assert entries[0].book.title == "Krojačev sin"
    assert entries[0].book.author == "Jelena Bačić Alimpić"
    assert entries[0].source == "Laguna Top lista"
    # ranks are sequential and match position, not any rank text on the page
    assert [e.rank for e in entries] == list(range(1, 41))
