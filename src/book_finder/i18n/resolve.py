from book_finder.i18n.strings import SUPPORTED_LANGUAGES

_TAG_ALIASES = {
    "sr": "sr-latn",
    "sr-latn": "sr-latn",
    "sr-cyrl": "sr-cyrl",
    "en": "en",
}


def _parse_accept_language(header: str) -> list[str]:
    entries = []
    for part in header.split(","):
        tag, _, params = part.strip().partition(";")
        quality = 1.0
        for param in params.split(";"):
            if param.strip().startswith("q="):
                try:
                    quality = float(param.strip()[2:])
                except ValueError:
                    quality = 1.0
        entries.append((quality, tag.strip().lower()))
    entries.sort(key=lambda entry: entry[0], reverse=True)
    return [tag for _, tag in entries]


def _match_accept_language(header: str) -> str | None:
    for tag in _parse_accept_language(header):
        matched = _TAG_ALIASES.get(tag)
        if matched is not None:
            return matched
    return None


def resolve_language(
    query_param: str | None,
    cookie: str | None,
    accept_language: str | None,
) -> str:
    if query_param in SUPPORTED_LANGUAGES:
        return query_param
    if cookie in SUPPORTED_LANGUAGES:
        return cookie
    if accept_language is not None:
        matched = _match_accept_language(accept_language)
        if matched is not None:
            return matched
    return "en"
