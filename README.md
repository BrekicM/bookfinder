# Book Finder

Finds the most popular books by genre and checks live in-stock availability,
price, and edition language across Serbian bookstores (Laguna, Vulkan, Delfi,
Booka).

See [CONTEXT.md](CONTEXT.md) for the domain model and [docs/adr/](docs/adr/)
for the key design decisions.

## Status

MVP complete: browse the 9 fixed genres (Global popularity via Open Library,
Serbian bestseller data via Laguna + Vulkan where available), free-text
search with disambiguation (merging Open Library with all four bookstores'
own catalogs, so domestic-only titles are still findable), and live per-book
availability/price/language checks across all four stores (see ADR 0004 for
how Delfi was added post-MVP, and ADR 0009 for Booka). A wishlist lets you
save book titles/authors locally and revisit them later. The UI is a
book-themed, mobile-friendly design with light/dark mode.

## Install

You only need `uv` — it manages Python itself, so there's nothing to install
separately even if Python isn't already on your machine.

**1. Install uv**

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart your terminal afterwards, then confirm it installed:

```bash
uv --version
```

(Full instructions/alternatives at [docs.astral.sh/uv/getting-started/installation](https://docs.astral.sh/uv/getting-started/installation/).)

**2. Get the code**

```bash
git clone https://github.com/BrekicM/bookfinder.git
cd bookfinder
```

No git? Download and extract the ZIP instead, then `cd` into the extracted
folder: https://github.com/BrekicM/bookfinder/archive/refs/heads/main.zip

**3. Install dependencies**

```bash
uv sync
```

This downloads the exact Python version the project needs (3.12+) if it
isn't already on your machine, plus every dependency, all sandboxed to this
project.

## Run it

```bash
uv run uvicorn book_finder.main:app --port 8123
```

Then open http://127.0.0.1:8123/ in your browser. Stop the server with
Ctrl+C.

## Use it

- **Browse** — pick a genre from the home page to see Global and Serbian
  popularity lists.
- **Search** — type a title or author; if there's more than one match,
  you'll be asked to pick the right one.
- **Check a book** — its page shows live availability, price, language, and
  format at each of the three stores, with a link to buy.
- **Wishlist** — click "Add to Wishlist" on a book's page to save it; find
  it again anytime from the Wishlist link in the nav.
- **Language** — switch the UI between English, Serbian (Latin), and Serbian
  (Cyrillic) via the EN / SR / SR-ĆIR links in the nav; your choice is
  remembered on your next visit. Book titles, authors, and your search text
  are never translated.

## Test

```bash
uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
```

Optional API keys (`.env`, see `.env.example`) enrich Global popularity data
later; the app works without them.
