# Language is selected via query param, not a URL path prefix

The conventional i18n pattern is a path prefix (`/sr-latn/genres/fantasy`), which every route in the app would need restructuring to support. This app is single-user with no public catalog or SEO surface to optimize for (see [CONTEXT.md](../../CONTEXT.md) — it's a personal availability-checker), so the SEO benefit of path prefixes buys nothing here. A `?lang=` query param achieves the same goal — a shareable, bookmarkable link that carries the language — purely additively, with no routing changes.
