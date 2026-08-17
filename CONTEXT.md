# Book Finder

An app that surfaces the most popular books by genre, then checks live in-stock availability, price, and edition language across Serbian bookstores.

## Language

**Book**:
A literary work identified by title and author (e.g. "1984" by George Orwell). Genre and popularity are properties of the Book, not of any single edition.
_Avoid_: Title, Work

**Edition**:
A specific listing of a Book at one Bookstore — carries its own price, language, and stock status. A Book may have several Editions across stores (e.g. a Serbian translation at Laguna, an English original at Vulkan).
_Avoid_: Listing, Product, Copy

**Bookstore**:
One of the Serbian retailers the app checks for Editions: Laguna, Vulkan, Delfi (see ADR 0004 — Delfi was briefly deferred by ADR 0003, then added once a real search API was found).
_Avoid_: Store, Retailer, Shop

**Popularity**:
The ranking signal used to sort Books within a Genre, computed independently as **Global** (international signals like bestseller rank, ratings, or want-to-read counts) and **Serbian** (each Bookstore's own published "Top lista" data) — shown as separate lists, never merged. A Genre missing Serbian data states that explicitly rather than falling back silently to Global; store-native bestseller categories are best-effort mapped onto the app's fixed Genre list.
_Avoid_: Ranking, Rating (a Rating is one possible input to Global Popularity, not the concept itself)

**Availability**:
Whether a Bookstore currently has an Edition in stock, checked live at the moment of the query (not cached) — not merely whether the store carries the title at all. The app does not distinguish *why* an Edition is unavailable (never carried vs. temporarily out of stock); both surface as a single "not available" result. This is the app's core purpose: finding books that can actually be bought right now.
_Avoid_: "Carried by", "listed at" (these describe catalog presence, not Availability)

**Genre**:
One of a fixed, curated set of categories used to group and browse Books: Fiction, Fantasy, Sci-Fi, Mystery/Thriller, Romance, Non-Fiction, Young Adult, Children's, Programming/Tech. Not derived dynamically from any external data source's taxonomy.
_Avoid_: Category, Tag, Subject

**Wishlist**:
A persisted set of Books the user has saved to look up again later, identified the same way as everywhere else (title+author, deduplicated). The app is single-user with no accounts, so there is exactly one Wishlist, stored locally rather than cached — unlike Popularity/catalog data, it never expires or gets refetched.
_Avoid_: Favorites, Saved, Cart (there's no purchase flow — this app only checks availability elsewhere)
