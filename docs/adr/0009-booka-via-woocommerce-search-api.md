# Booka integrates via WooCommerce's public search API, not its sitemap

Unlike Laguna/Vulkan (sitemap-only) or Delfi (search-only, reverse-engineered), Booka exposes both a working sitemap and a documented search API — the WooCommerce Store API (`/wp-json/wc/store/v1/products?search=`), confirmed via plain HTTP GET returning price, stock, and RSD pricing directly. `BookaClient` overrides `find_editions()` to call this endpoint directly, the same shape as `DelfiClient`, rather than reusing `BookstoreClient`'s sitemap-and-shortlist base.

The search API was chosen over the sitemap-and-catalog approach because it's an officially documented WordPress/WooCommerce endpoint (lower risk of silently breaking than Delfi's reverse-engineered one), needs no catalog cache to keep fresh, and returns price/stock in a single call instead of a candidate-shortlist-then-fetch round trip. The trade-off: author name isn't inline in the search response and needs a second lookup against the `pisac` taxonomy endpoint.

Booka's sitemap (`product-sitemap.xml`) does exist and does mix book and non-book products, so it remains a viable fallback pattern if the search API ever stops working — but the sitemap-and-shortlist path was not built, since only one integration path is needed per store.
