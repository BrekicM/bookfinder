from pathlib import Path

from book_finder.stores.sitemap import parse_sitemap_urls

FIXTURES = Path(__file__).parent.parent / "parsing" / "fixtures"


def test_parses_empty_sitemap_returns_empty_list() -> None:
    xml = '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>'
    assert parse_sitemap_urls(xml) == []


def test_parses_urls_from_real_sitemap_sample() -> None:
    xml = (FIXTURES / "laguna_sitemap_sample.xml").read_text(encoding="utf-8")
    urls = parse_sitemap_urls(xml)

    assert len(urls) == 8
    assert "https://laguna.rs/proizvodi/knjige/urgum-sekiras/" in urls


def test_malformed_xml_returns_empty_list_instead_of_raising() -> None:
    assert parse_sitemap_urls("<not><valid") == []
