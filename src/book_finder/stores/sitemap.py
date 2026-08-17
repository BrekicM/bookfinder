from xml.etree import ElementTree

_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def parse_sitemap_urls(xml: str) -> list[str]:
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError:
        return []

    return [loc.text.strip() for loc in root.findall(".//sm:url/sm:loc", _NS) if loc.text]
