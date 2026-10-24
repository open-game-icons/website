# AGENTS.md

Zola static site for browsing icons.

## Setup

Dependencies:

- Zola 0.23.6 and Python 3 (required to build the site)
- `just` (recommended for convenience)
- `dprint` and `uv` (optional; `uvx` runs djLint for template formatting)

Build the site with `just build` (includes DB and content stub regeneration, and post-build cleanup; fast).

## Architecture

- `templates/`: Tera templates (`base.html`, `index.html`, `page.html`, `icon.html`, `tag_page.html`, `404.html`, `partials/`)
- `static/`: copied to `public/`; `scripts/post_build.py` prunes build-only files after the build
  - `static/assets/icons/`: subrepo (`man 1 git-subrepo`) containing icon SVGs; only the SVG directories and license files are published
  - `static/assets/icons/icons.db`: SQLite DB of icon metadata, built from `static/assets/icons/icons.sql`; source only, not published
    - Tables: `icons`, `authors`, `licenses`, `tags`, `icon_tags`, `icon_keywords`
  - `static/assets/js/search.js`: client-side search (filters icon grid by keyword match)
- `scripts/generate.py`
  - Generates content stubs in `content/generated/` and lookup data in `data/generated/`
  - Generates `static/search-index.json` for the client-side search
  - Declares legacy `.html` URLs as Zola aliases on each generated page
- `scripts/post_build.py`: post-processes the build
  - Removes the icon DB, `icons.sql`, shell scripts, docs, and SVGO config copied from `static/assets/icons`
  - Does not move generated pages; canonical pages and aliases are produced by Zola
- `scripts/check.py`: validates built page counts, aliases, search entries, and internal links

Canonical URLs are Zola's pretty routes:

- Per-icon pages at `/1x1/{author}/{icon_id}/`
- Tag pages at `/tags/{tag_id}/`

The old `.html` paths (`/1x1/{author}/{icon_id}.html`, `/tags/{tag_id}.html`)
are Zola aliases: small client-side redirect files, not HTTP 301s. Internal
links use the canonical pretty URLs. The redirect target is built from
`base_url`; `just serve` builds with a local base URL so aliases work locally.

Generated paths (`public/`, `content/generated/`, `data/generated/`, `static/search-index.json`) are gitignored.

## Cleanup and validation

- `just fmt` to format
- `just check` to build the site + run static checks
