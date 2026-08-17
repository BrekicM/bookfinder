from pathlib import Path

from book_finder.popularity.serbian_sources import parse_vulkan_top_liste

FIXTURES = Path(__file__).parent / "fixtures"


def test_returns_empty_list_when_no_heading_found() -> None:
    assert parse_vulkan_top_liste("<html><body>nothing here</body></html>") == []


def test_parses_real_romani_list_page() -> None:
    html = (FIXTURES / "vulkan_top_liste_romani.html").read_text(encoding="utf-8")
    entries = parse_vulkan_top_liste(html)

    assert len(entries) == 30
    assert entries[0].rank == 1
    assert entries[0].book.title == "PRIZNANJE"
    assert entries[0].book.author == "Miodrag Majić"
    assert entries[0].source == "Vulkan Top lista"
    # unrelated footer/nav items (Vulkan klub, Gift kartica, ...) have no
    # author-name element and must not leak into the list
    titles = [e.book.title for e in entries]
    assert "Vulkan klub" not in titles
    assert "Gift kartica" not in titles
    assert [e.rank for e in entries] == list(range(1, 31))
