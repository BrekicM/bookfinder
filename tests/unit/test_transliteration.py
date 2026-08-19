# Test list:
# - empty string -> empty string
# - plain word, no diacritics/digraphs
# - single diacritic letter (š)
# - digraph lj (lowercase)
# - digraph nj (lowercase)
# - digraph dž (lowercase)
# - digraph titlecase (Nj, Lj, Dž)
# - digraph all-caps (NJ, LJ, DŽ)
# - non-alphabet characters pass through unchanged (digits, punctuation, spaces)

from book_finder.i18n.transliteration import to_cyrillic


def test_empty_string_is_unchanged() -> None:
    assert to_cyrillic("") == ""


def test_plain_word_maps_letter_by_letter() -> None:
    assert to_cyrillic("sto") == "сто"


def test_uppercase_letters_map_to_uppercase_cyrillic() -> None:
    assert to_cyrillic("Beograd") == "Београд"


def test_lj_digraph_maps_to_a_single_cyrillic_letter() -> None:
    assert to_cyrillic("ljubav") == "љубав"


def test_nj_digraph_maps_to_a_single_cyrillic_letter() -> None:
    assert to_cyrillic("konj") == "коњ"


def test_dz_digraph_maps_to_a_single_cyrillic_letter() -> None:
    assert to_cyrillic("džem") == "џем"


def test_titlecase_digraph_maps_to_titlecase_cyrillic() -> None:
    assert to_cyrillic("Njegoš") == "Његош"


def test_allcaps_digraph_maps_to_allcaps_cyrillic() -> None:
    assert to_cyrillic("LJUBAV") == "ЉУБАВ"


def test_non_alphabet_characters_pass_through_unchanged() -> None:
    assert to_cyrillic("Knjiga 1: Uvod!") == "Књига 1: Увод!"
