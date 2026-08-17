# Book Finder

Finds the most popular books by genre and checks live in-stock availability,
price, and edition language across Serbian bookstores (Laguna, Vulkan).

See [CONTEXT.md](CONTEXT.md) for the domain model and [docs/adr/](docs/adr/)
for the key design decisions.

## Status

MVP complete: browse the 9 fixed genres (Global popularity via Open Library,
Serbian bestseller data via Laguna + Vulkan where available), free-text
search with disambiguation, and live per-book availability/price/language
checks across both stores. Delfi is deferred post-MVP (see ADR 0003).

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
