# Book Finder

Finds the most popular books by genre and checks live in-stock availability,
price, and edition language across Serbian bookstores (Laguna, Vulkan, Delfi).

See [CONTEXT.md](CONTEXT.md) for the domain model and [docs/adr/](docs/adr/)
for the key design decisions.

## Status

MVP complete: browse the 9 fixed genres (Global popularity via Open Library,
Serbian bestseller data via Laguna + Vulkan where available), free-text
search with disambiguation, and live per-book availability/price/language
checks across all three stores (see ADR 0004 for how Delfi was added post-MVP).
A wishlist lets you save book titles/authors locally and revisit them later.

## Run it

```bash
uv sync
uv run uvicorn book_finder.main:app --port 8123
```

Then open http://127.0.0.1:8123/

## Test

```bash
uv run pytest
uv run ruff check src tests
```

Optional API keys (`.env`, see `.env.example`) enrich Global popularity data
later; the app works without them.
