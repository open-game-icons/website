# AGENTS.md

Jekyll static site for browsing icons.

## Setup

```sh
git submodule update --init --recursive
bundle install
sqlite3 _db/icons.db < _db/icons.sql # rerun if icons.sql changes
```

## Build

```sh
bundle exec jekyll build
```

## Architecture

- `assets/icons/`: submodule containing icon SVGs
- `_db/icons.db`: SQLite DB of icon metadata, built from `_db/icons.sql`
	- Tables: `icons`, `authors`, `licenses`, `tags`, `icon_tags`, `icon_keywords`
	- View: `tag_icon_counts`
- `_config.yml`: declares `icon_pages` and `tag_pages` collections, wired to DB queries via `jekyll-sqlite`
	- Per-icon pages at `/1x1/{author}/{icon_id}/`
	- Tag pages at `/tags/{tag_id}/`
	- Data arrays `tag_icon_counts` and `all_tag_icons` for Liquid `where` filter lookups
- `_plugins/search_index_generator.rb`: builds `site.data.search_index` from the database for client-side search
- `assets/js/search.js`: client-side search (filters icon grid by keyword match)
- `search-index.json`: outputs `site.data.search_index` as JSON for the client

## Conventions

- Format CSS and JavaScript (not HTML) with `prettier`.
- Preserve explanatory comments in Ruby code to keep the code approachable for non-Ruby developers.
  Add or update comments when changing logic, and do not remove existing comments unless they are obsolete.
