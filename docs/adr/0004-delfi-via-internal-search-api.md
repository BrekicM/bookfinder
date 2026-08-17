# Delfi integrates via its internal search API, not a headless browser

ADR 0003 deferred Delfi because its product pages are a client-rendered SPA with nothing in the raw HTML — that part is still true. But its *search box* turned out to call a real, unauthenticated internal JSON endpoint (`pc-frontend-api/search/quick-search-products/{category}/{query}`) that returns full product data — title, author, price, live availability, format — in one call, with no separate product-page fetch needed at all.

This was found by loading the real site in a headless browser once, during development, and recording which network request the search box actually fired — not by guessing endpoint names (several plausible guesses, e.g. `pc-frontend-api/book?id=`, returned the same generic homepage payload regardless of parameters). Playwright was a one-time investigation tool here, not a runtime dependency: `DelfiClient` uses plain `httpx`, like Laguna and Vulkan.

This also makes Delfi's integration simpler than the other two: since the search actually works, `DelfiClient` doesn't need the sitemap-cache-and-shortlist approach `BookstoreClient` provides for Laguna/Vulkan (see `stores/base.py`) — it overrides `find_editions()` directly with a single live search call.

## Update: the `{category}` segment matters, and "all categories" isn't safe

The `{category}` placeholder above isn't decorative — the endpoint's ranking is scoped by it, and it's capped at a handful of results per call. Querying `Sve kategorije` ("all categories") ranks across Delfi's *entire* catalog, not just books: for a heavily-merchandised franchise (mugs, stickers, plushies, earbuds...), real books can be crowded out of the results entirely, e.g. searching "harry potter" or "gospodar prstenova" (Lord of the Rings) under `Sve kategorije` returned zero books.

Probing the category segment with known Serbian category names found two that reliably return actual books: `Knjiga` (domestic) and `Strana knjiga` (foreign/translated) — no combined-category value works, so `fetch_book_editions()` queries both concurrently and merges, deduping by product URL. This applies to both the availability check (`find_editions`) and free-text search (`search_delfi_books`), which now share that function.
