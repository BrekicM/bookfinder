# Test list:
# - t() returns the English string for lang "en"
# - t() returns the Serbian Latin string for lang "sr-latn"
# - t() returns a transliterated Cyrillic string for lang "sr-cyrl"
# - t() falls back to English when the key has no Serbian Latin translation
# - t() falls back to English (untransliterated) for sr-cyrl when the key has no Serbian Latin translation
# - unknown/unsupported lang falls back to English
# - EN and SR_LATN have exactly the same set of keys (parity)

from book_finder.i18n.strings import EN, SR_LATN, t


def test_returns_english_string_for_en() -> None:
    assert t("nav_wishlist", "en") == EN["nav_wishlist"]


def test_returns_serbian_latin_string_for_sr_latn() -> None:
    assert t("nav_wishlist", "sr-latn") == SR_LATN["nav_wishlist"]


def test_returns_transliterated_cyrillic_string_for_sr_cyrl() -> None:
    assert t("nav_wishlist", "sr-cyrl") == "Листа жеља"


def test_falls_back_to_english_for_sr_latn_when_key_missing(monkeypatch) -> None:
    monkeypatch.setitem(EN, "only_in_english", "Only in English")
    assert t("only_in_english", "sr-latn") == "Only in English"


def test_falls_back_to_english_untransliterated_for_sr_cyrl_when_key_missing(monkeypatch) -> None:
    monkeypatch.setitem(EN, "only_in_english", "Only in English")
    assert t("only_in_english", "sr-cyrl") == "Only in English"


def test_unknown_lang_falls_back_to_english() -> None:
    assert t("nav_wishlist", "fr") == EN["nav_wishlist"]


def test_en_and_sr_latn_have_the_same_keys() -> None:
    assert EN.keys() == SR_LATN.keys()


def test_format_arg_is_substituted_into_cyrillic_heading_without_crashing() -> None:
    result = t("search_results_heading", "sr-cyrl", "Nenad Gugl")

    assert "Nenad Gugl" in result


def test_format_arg_is_not_itself_transliterated() -> None:
    result = t("search_results_heading", "sr-cyrl", "Ljubav")

    assert "Ljubav" in result
    assert "Љубав" not in result
