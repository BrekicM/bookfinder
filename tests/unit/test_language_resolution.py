# Test list:
# - nothing provided at all -> "en"
# - explicit query param wins over everything
# - unsupported query param is ignored, falls through
# - cookie is used when there's no query param
# - unsupported cookie is ignored, falls through
# - Accept-Language exact match (e.g. "sr-latn") is used when no param/cookie
# - Accept-Language bare "sr" resolves to "sr-latn"
# - Accept-Language with no supported match falls back to "en"
# - Accept-Language honors preference order (q-values)

from book_finder.i18n.resolve import resolve_language


def test_nothing_provided_defaults_to_english() -> None:
    assert resolve_language(query_param=None, cookie=None, accept_language=None) == "en"


def test_query_param_wins_over_everything() -> None:
    result = resolve_language(query_param="sr-cyrl", cookie="en", accept_language="en")
    assert result == "sr-cyrl"


def test_unsupported_query_param_falls_through_to_cookie() -> None:
    result = resolve_language(query_param="fr", cookie="sr-latn", accept_language="en")
    assert result == "sr-latn"


def test_cookie_used_when_no_query_param() -> None:
    result = resolve_language(query_param=None, cookie="sr-cyrl", accept_language="en")
    assert result == "sr-cyrl"


def test_unsupported_cookie_falls_through_to_accept_language() -> None:
    result = resolve_language(query_param=None, cookie="fr", accept_language="sr-latn")
    assert result == "sr-latn"


def test_bare_sr_accept_language_resolves_to_serbian_latin() -> None:
    result = resolve_language(query_param=None, cookie=None, accept_language="sr")
    assert result == "sr-latn"


def test_accept_language_with_no_supported_match_falls_back_to_english() -> None:
    result = resolve_language(query_param=None, cookie=None, accept_language="fr-FR")
    assert result == "en"


def test_accept_language_honors_q_value_preference_order() -> None:
    result = resolve_language(query_param=None, cookie=None, accept_language="fr;q=0.9,sr-cyrl;q=0.5")
    assert result == "sr-cyrl"
