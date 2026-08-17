# Book Finder

Finds the most popular books by genre and checks live in-stock availability,
price, and edition language across Serbian bookstores (Laguna, Vulkan).

See [CONTEXT.md](CONTEXT.md) for the domain model and [docs/adr/](docs/adr/)
for the key design decisions.

## Status

MVP in progress. Currently working: live per-book availability/price checks
across both stores, with catalog-based matching (neither store exposes a
real search API). Not yet built: genre browsing, free-text search, and a
homepage — see the plan history for the full roadmap.

## Run it

```bash
uv sync
uv run uvicorn book_finder.main:app --port 8123
```

Then, since there's no homepage yet, hit the book-detail route directly:

```
http://127.0.0.1:8123/books?title=Kosingas 2: Bezdanj&author=Aleksandar Tesic
```

## Test

```bash
uv run pytest
uv run ruff check src tests
```

Optional API keys (`.env`, see `.env.example`) enrich Global popularity data
later; the app works without them.
