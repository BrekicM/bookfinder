from book_finder.domain.models import Genre

# Neither store exposes a genre-filterable feed — these are the specific,
# individually-confirmed category-list pages found during implementation.
# A genre with no entry here has no Serbian data for that store, by design
# (CONTEXT.md: missing Serbian data is stated explicitly, never guessed).

LAGUNA_GENRE_URLS: dict[Genre, str] = {
    Genre.FICTION: "https://laguna.rs/top-liste/",
    Genre.NON_FICTION: "https://laguna.rs/top-liste-publicistika/",
    Genre.CHILDRENS: "https://laguna.rs/top-liste-mala-laguna/",
}

VULKAN_GENRE_URLS: dict[Genre, str] = {
    Genre.FICTION: "https://www.knjizare-vulkan.rs/proizvodi/top-lista-romani-10",
    Genre.FANTASY: "https://www.knjizare-vulkan.rs/proizvodi/top-lista-10-fantastika",
    Genre.ROMANCE: "https://www.knjizare-vulkan.rs/proizvodi/top-lista-ljubavni-romani-10",
    Genre.MYSTERY_THRILLER: "https://www.knjizare-vulkan.rs/proizvodi/top-lista-trileri-10",
    Genre.NON_FICTION: "https://www.knjizare-vulkan.rs/proizvodi/top-lista-popularna-psihologije-10",
    Genre.CHILDRENS: "https://www.knjizare-vulkan.rs/domace-decje-knjige/top-lista-decije-knjige-50",
}
