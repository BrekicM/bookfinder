# Booka integrates via WooCommerce's public search API, not its sitemap

Unlike Laguna/Vulkan (sitemap-only) or Delfi (search-only, reverse-engineered), Booka exposes both a working sitemap and a documented search API — the WooCommerce Store API (`/wp-json/wc/store/v1/products?search=`), confirmed via plain HTTP GET returning price, stock, and RSD pricing directly. `BookaClient` implements `find_editions()` by calling this endpoint directly, the same shape as `DelfiClient`, rather than reusing the sitemap-and-shortlist base (`CatalogBookstoreClient`).

The search API was chosen over the sitemap-and-catalog approach because it's an officially documented WordPress/WooCommerce endpoint (lower risk of silently breaking than Delfi's reverse-engineered one), needs no catalog cache to keep fresh, and returns price/stock in a single call instead of a candidate-shortlist-then-fetch round trip. The trade-off: author name isn't inline in the search response and needs a second lookup against the `pisac` taxonomy endpoint.

Booka's sitemap (`product-sitemap.xml`) does exist and does mix book and non-book products, so it remains a viable fallback pattern if the search API ever stops working — but the sitemap-and-shortlist path was not built, since only one integration path is needed per store.

## Update: the client hierarchy was split

As with Delfi (ADR 0004), `BookaClient` used to carry a `_parse_product_page()` stub raising `NotImplementedError`, because the old `BookstoreClient` base *was* the sitemap-catalog pipeline. The sitemap machinery moved to `CatalogBookstoreClient`, leaving `BookstoreClient` as just `find_editions()` + `search_titles()`. `BookaClient` now implements both directly; its `search_titles()` adapts `search_books()` (which keeps the per-candidate `pisac` author resolution described above) from `list[Edition]` to `list[Book]`.
