# AGENTS.md

Zola static site for browsing icons.

## Setup

Install Zola 0.23.6 and `just`.
Python 3 is used by the build scripts.

```sh
just db # rerun if icons.sql changes
just build
```

`just build` runs `scripts/generate.py`, then `zola build`, then `scripts/post_build.py`.
`just serve` builds and serves `public/`; `zola serve` alone uses pretty URLs and should only be used for template iteration.

## Architecture

- `static/`: copied to `public/`; `scripts/post_build.py` prunes build-only files after the build
  - `static/assets/icons/`: subrepo (`man 1 git-subrepo`) containing icon SVGs; only the SVG directories and `license.txt` are published
  - `static/assets/icons/icons.db`: SQLite DB of icon metadata, built from `static/assets/icons/icons.sql`; source only, not published
    - Tables: `icons`, `authors`, `licenses`, `tags`, `icon_tags`, `icon_keywords`
  - `static/assets/js/search.js`: client-side search (filters icon grid by keyword match)
- `scripts/generate.py`
  - Generates content stubs in `content/generated/` and lookup data in `data/generated/`
  - Generates `static/search-index.json` for the client-side search
- `scripts/post_build.py`: post-processes the build
  - Moves generated pages from Zola's pretty routes to the legacy `.html` routes matching Game-icons.net
    - Per-icon pages at `/1x1/{author}/{icon_id}.html`
    - Tag pages at `/tags/{tag_id}.html`
  - Removes the icon DB, `icons.sql`, shell scripts, docs, and SVGO config copied from `static/assets/icons`
- `scripts/check.py`: validates built page counts, search entries, and internal links
- `templates/`: Tera templates (`base.html`, `index.html`, `page.html`, `icon.html`, `tag_page.html`, `404.html`, `partials/`)

Generated paths (`public/`, `content/generated/`, `data/generated/`, `static/search-index.json`) are gitignored.
Do not use `page.url` or `page.permalink` in templates: the public URLs are `.html` paths created by the post-build step.

## Conventions

- Format CSS and JavaScript (not HTML) with `prettier`.
