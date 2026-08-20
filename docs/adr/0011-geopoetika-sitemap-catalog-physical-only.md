# Geopoetika: sitemap-based catalog, physical books only, discounted price

Geopoetika is a publisher's own web shop (Belgrade, est. 1993), not a marketplace. Unlike Čarobna knjiga, there's no mixed-content-type ambiguity to resolve at the URL level: every product page follows the single `/o-knjizi/{id}/{slug}` pattern, and `robots.txt` (`User-agent: *` / `Disallow:` — nothing blocked) exposes a flat `sitemap.xml` listing every product URL directly, alongside a handful of static pages (home, `/books`, `/authors`, `/articles`, `/page/o-nama`, `/page/kontakt`). `GeopoetikaClient` therefore uses `CatalogBookstoreClient`'s *default* `_fetch_catalog_urls` (fetch `sitemap_url`, parse as sitemap XML) unmodified — no override needed, unlike Čarobna knjiga's genre-page crawl. The static pages are filtered out via `_is_book_url` checking for the `/o-knjizi/` prefix.

The site does show a non-book "Gift" category (mugs, bookmarks, notebooks) on its homepage, but those items don't appear in the sitemap or in `/books` — confirmed by checking that every URL in both sources follows `/o-knjizi/`. So no genre/category filtering is needed to keep the catalog books-only; the sitemap is already clean.

No usable live search was found (`?s=` and `/pretraga?q=` both fail to return results), so — as with Laguna, Vulkan, and Čarobna knjiga — every candidate still needs its own product-page fetch via the cached-catalog-and-shortlist shape rather than a direct-API client.

Geopoetika also runs a separate mobile app for ebooks, entirely distinct from the web catalog scraped here. That app is out of scope — `GeopoetikaClient` only surfaces physical editions listed on geopoetika.com.

Price is read as the discounted figure (e.g. `-20%: 1144 din`) when a discount is shown, not the struck-through list price — same convention as Čarobna knjiga's "Vaša cena": Edition.price reflects what a buyer actually pays right now.
