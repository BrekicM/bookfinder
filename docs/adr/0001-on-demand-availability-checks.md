# On-demand availability checks, not periodic caching

Availability means whether a book is in stock *right now*, and this is a low-volume personal tool, so the app checks each Bookstore live at query time rather than running a scheduled scraping pipeline with a cached "checked X ago" status. This trades a slower per-search response for always-accurate results and avoids operating a background refresh job.
