# AGENTS.md

Zola static site for browsing icons.

## Setup

Dependencies:

- Zola 0.23.6 and Python 3.11+ (required to build the site)
- `just` (recommended for convenience)
- `dprint` and `uv` (optional; `uvx` runs djLint for template formatting)

Build the site with `just build` (includes DB and content stub regeneration; fast).
There is no post-build pruning step: `just serve` runs `zola serve` against the
same generated static staging tree as the production build. Run `just generate`
first if `static/assets/icons/` is missing.

## Architecture

- `templates/`: Tera templates (`base.html`, `index.html`, `page.html`, `icon.html`, `tag_page.html`, `404.html`, `partials/`)
- `static/`: copied to `public/`
  - `static/assets/icons/`: generated staging directory (gitignored) containing symlinks to the publishable icon assets; Zola follows the symlinks and copies regular files into `public/`
  - `static/assets/js/search.js`: client-side search (filters icon grid and tag links by keyword match; reveals homepage-hidden items when they match)
- `icons/`: subrepo (`man 1 git-subrepo`) containing the icon SVGs and source files
  - `icons/icons.db`: SQLite DB of icon metadata, built from `icons/icons.sql`; source only, not published
    - Tables: `icons`, `authors`, `licenses`, `tags`, `icon_tags`, `icon_keywords`
- `scripts/generate.py`
  - Generates content stubs in `content/generated/` and lookup data in `data/generated/`
  - Generates `static/search-index.json` for the client-side search
  - Marks icons with certain tags (`HOMEPAGE_HIDDEN_ICON_TAGS`) as hidden on the homepage grid
  - Declares legacy `.html` URLs as Zola aliases on each generated page
  - Rebuilds `static/assets/icons` with symlinks to the SVG directories and license files
- `scripts/check.py`: validates built page counts, aliases, search entries, homepage visibility, and internal links

Canonical URLs are Zola's pretty routes:

- Per-icon pages at `/1x1/{author}/{icon_id}/`
- Tag pages at `/tags/{tag_id}/`

The old `.html` paths (`/1x1/{author}/{icon_id}.html`, `/tags/{tag_id}.html`)
are Zola aliases: small client-side redirect files, not HTTP 301s. Internal
links use the canonical pretty URLs. The redirect target is built from
`base_url`; `zola serve` uses its local server URL so aliases work locally.

Generated paths (`public/`, `content/generated/`, `data/generated/`,
`static/search-index.json`, `static/assets/icons/`) are gitignored.

## Cleanup and validation

- `just fmt` to format
- `just check` to build the site + run static checks
