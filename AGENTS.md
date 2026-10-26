# AGENTS.md

Zola static site for browsing icons.

## Setup

Dependencies:

- Zola 0.23.6 and Python 3.11+ (required to build the site)
- Bun 1.4.x (required for the TypeScript bundle; version pinned in `.bun-version`)
- `just` (recommended for convenience)
- `dprint` and `uv` (optional; `uvx` runs djLint for template formatting)

Build the site with `just build` (includes DB and content stub regeneration plus the TypeScript bundle; fast).
There is no post-build pruning step: `just serve` runs `zola serve` against the
same generated static staging tree as the production build. Run `just generate`
and `just js` first if `static/assets/icons/` or `static/assets/js/` is missing.

## Architecture

- `templates/`: Tera templates and partials
- `src/ts/`: authored TypeScript; Bun bundles it to ES modules loaded with `<script type="module">` in `static/assets/js/`
  - `src/ts/search.ts`: filters icon grid and tag links by keyword match and reveals homepage-hidden items when they match
  - `src/ts/icon-download.ts`: renders PNGs for download, embeds metadata, and supports in-browser icon editing ("studio")
- `static/`: copied to `public/`
  - `static/assets/icons/`: generated staging directory (gitignored) containing symlinks to the publishable icon assets; Zola follows the symlinks and copies regular files into `public/`
  - `static/assets/js/`: generated ES module bundles and shared chunks from `src/ts/` (gitignored)
- `icons/`: subrepo (`man 1 git-subrepo`) containing the icon SVGs and source files
  - `icons/icons.db`: SQLite DB of icon metadata, built from `icons/icons.sql`; source only, not published
    - Tables: `icons`, `authors`, `licenses`, `tags`, `icon_tags`, `icon_keywords`
- `scripts/generate.py`
  - Generates content stubs in `content/generated/` and lookup data in `data/generated/`
  - Generates `static/search-index.json` for the client-side search
  - Marks icons with certain tags (`HOMEPAGE_HIDDEN_ICON_TAGS`) as hidden on the homepage grid
  - Declares legacy `.html` URLs as Zola aliases on icon and tag pages
  - Rebuilds `static/assets/icons` with symlinks to the SVG directories and license files
- `scripts/check.py`: validates built page counts, aliases, search entries, homepage visibility, and internal links

Canonical URLs are Zola's pretty routes:

- Per-icon pages at `/1x1/{author}/{icon_id}/`
- Author pages at `/1x1/{author}/`
- Tag pages at `/tags/{tag_id}/`

The old `.html` paths (`/1x1/{author}/{icon_id}.html`, `/tags/{tag_id}.html`)
are Zola aliases: small client-side redirect files, not HTTP 301s. Internal
links use the canonical pretty URLs. The redirect target is built from
`base_url`; `zola serve` uses its local server URL so aliases work locally.
Author pages are new routes with no legacy aliases.

Generated paths (`public/`, `content/generated/`, `data/generated/`,
`static/search-index.json`, `static/assets/icons/`, `static/assets/js/`) are gitignored.

## Cleanup and validation

- `just fmt` to format
- `just check` to build the site and run full checks (slower than a plain build)
  - Also checks formatting; no need to `just fmt` if it passes
