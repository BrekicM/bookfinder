from book_finder.i18n.transliteration import to_cyrillic

EN: dict[str, str] = {
    "brand": "Book Finder",
    "nav_wishlist": "Wishlist",
    "search_placeholder": "Search by title or author",
    "search_button": "Search",
    "browse_by_genre": "Browse by genre",
    "add_to_wishlist": "Add to Wishlist",
    "remove_from_wishlist": "Remove from Wishlist",
    "remove": "Remove",
    "available": "Available",
    "not_available": "Not available",
    "check_failed": "Check failed",
    "global_heading": "Global",
    "serbian_heading": "Serbian",
    "no_global_data": "No Global data for this genre right now.",
    "no_serbian_data": "No Serbian bestseller data for this genre.",
    "search_results_heading": 'Search results for "{0}"',
    "multiple_matches": "Multiple matches — which one did you mean?",
    "no_matches": "No matches found.",
    "wishlist_heading": "Wishlist",
    "wishlist_empty": "Your shelf is empty. Add books from their detail page.",
    "view_link": "view",
    "genre_fiction": "Fiction",
    "genre_fantasy": "Fantasy",
    "genre_sci_fi": "Sci-Fi",
    "genre_mystery_thriller": "Mystery/Thriller",
    "genre_romance": "Romance",
    "genre_non_fiction": "Non-Fiction",
    "genre_young_adult": "Young Adult",
    "genre_childrens": "Children's",
    "genre_programming_tech": "Programming/Tech",
}

SR_LATN: dict[str, str] = {
    "brand": "Book Finder",
    "nav_wishlist": "Lista želja",
    "search_placeholder": "Pretraga po naslovu ili autoru",
    "search_button": "Pretraga",
    "browse_by_genre": "Pregled po žanru",
    "add_to_wishlist": "Dodaj na listu želja",
    "remove_from_wishlist": "Ukloni sa liste želja",
    "remove": "Ukloni",
    "available": "Dostupno",
    "not_available": "Nije dostupno",
    "check_failed": "Provera neuspešna",
    "global_heading": "Globalno",
    "serbian_heading": "Srpsko",
    "no_global_data": "Trenutno nema globalnih podataka za ovaj žanr.",
    "no_serbian_data": "Nema podataka o srpskim bestselerima za ovaj žanr.",
    "search_results_heading": 'Rezultati pretrage za "{0}"',
    "multiple_matches": "Više poklapanja — na koje ste mislili?",
    "no_matches": "Nema pronađenih rezultata.",
    "wishlist_heading": "Lista želja",
    "wishlist_empty": "Vaša polica je prazna. Dodajte knjige sa njihove stranice.",
    "view_link": "pogledaj",
    "genre_fiction": "Fikcija",
    "genre_fantasy": "Fantastika",
    "genre_sci_fi": "Naučna fantastika",
    "genre_mystery_thriller": "Triler/Misterija",
    "genre_romance": "Ljubavni roman",
    "genre_non_fiction": "Publicistika",
    "genre_young_adult": "Tinejdžerski roman",
    "genre_childrens": "Dečije knjige",
    "genre_programming_tech": "Programiranje/Tehnologija",
}

SUPPORTED_LANGUAGES = ("en", "sr-latn", "sr-cyrl")

LANGUAGE_LABELS: dict[str, str] = {
    "en": "EN",
    "sr-latn": "SR",
    "sr-cyrl": "SR-ĆIR",
}


def t(key: str, lang: str, *args: str) -> str:
    if lang == "sr-latn":
        template = SR_LATN.get(key, EN[key])
    elif lang == "sr-cyrl":
        latn = SR_LATN.get(key)
        template = to_cyrillic(latn) if latn is not None else EN[key]
    else:
        template = EN[key]
    return template.format(*args) if args else template
