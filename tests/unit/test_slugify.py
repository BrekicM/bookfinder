from book_finder.stores.slugify import slugify


def test_slugifies_plain_ascii_title() -> None:
    assert slugify("1984") == "1984"


def test_replaces_punctuation_and_spaces_with_hyphens() -> None:
    assert slugify("Kosingas 2: Bezdanj") == "kosingas-2-bezdanj"


def test_strips_serbian_diacritics_matching_real_store_slugs() -> None:
    # confirmed against the real laguna.rs slug for this exact title
    assert slugify("Urgum Sekiraš") == "urgum-sekiras"


def test_collapses_repeated_separators_and_trims_edges() -> None:
    assert slugify("  Neko   Ime -- Nešto  ") == "neko-ime-nesto"


def test_strips_dj_producing_diacritic() -> None:
    assert slugify("Đavo") == "davo"
