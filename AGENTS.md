# AGENTS.md

Zola static site for browsing icons.

## Setup

Install Zola 0.23.6 and `just`.
Python 3 is used by the build scripts.

```sh
just db # rerun if icons.sql changes
just build
```

`just build` runs `scripts/generate.py`, then `zola build`, then `scripts/flatten_urls.py`.
`just serve` builds and serves `public/`; `zola serve` alone uses pretty URLs and should only be used for template iteration.

## Architecture

- `assets/icons/`: subrepo (`man 1 git-subrepo`) containing icon SVGs
- `assets/icons/icons.db`: SQLite DB of icon metadata, built from `assets/icons/icons.sql`
  - Tables: `icons`, `authors`, `licenses`, `tags`, `icon_tags`, `icon_keywords`
- `scripts/generate.py`
  - Generates content stubs in `content/generated/` and lookup data in `data/generated/`
  - Generates `static/search-index.json` for the client-side search
- `scripts/flatten_urls.py`: moves generated pages from Zola's pretty routes to the legacy `.html` routes matching Game-icons.net
  - Per-icon pages at `/1x1/{author}/{icon_id}.html`
  - Tag pages at `/tags/{tag_id}.html`
- `templates/`: Tera templates (`base.html`, `index.html`, `page.html`, `icon.html`, `tag_page.html`, `404.html`, `partials/`)
- `scripts/check_links.py`: validates built page counts, search entries, and internal links
- `static/`: published verbatim; `static/assets` is a symlink to `../assets`
- `assets/js/search.js`: client-side search (filters icon grid by keyword match)

Generated paths (`public/`, `content/generated/`, `data/generated/`, `static/search-index.json`) are gitignored.
Do not use `page.url` or `page.permalink` in templates: the public URLs are `.html` paths created by the flattening step.

## Conventions

- Format CSS and JavaScript (not HTML) with `prettier`.
