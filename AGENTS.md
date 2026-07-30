# AGENTS.md

Jekyll static site for browsing icons.

## Setup

```sh
git submodule update --init --recursive
bundle install
(cd assets/icons && ./rebuild_db.sh) # rerun if icons.sql changes
```

## Build

```sh
bundle exec jekyll build
```

## Architecture

- `assets/icons/`: submodule containing icon SVGs
- `assets/icons/icons.db`: SQLite DB of icon metadata, built from `assets/icons/icons.sql`
	- Tables: `icons`, `authors`, `licenses`, `tags`, `icon_tags`, `icon_keywords`
- `_config.yml`: declares `icon_pages` and `tag_pages` collections, wired to DB queries via `jekyll-sqlite`
	- Per-icon pages at `/1x1/{author}/{icon_id}/`
	- Tag pages at `/tags/{tag_id}/`
	- Data arrays `tag_info_array`, `tag_icons_array`, `search_index_array`
- `_plugins/data_mapper.rb`: converts `jekyll-sqlite` `*_array` data into hashes (`tag_info`, `tag_icons`, `search_index`) for faster Liquid rendering and client-side search
- `assets/js/search.js`: client-side search (filters icon grid by keyword match)
- `search-index.json`: outputs `site.data.search_index` as JSON for the client

## Conventions

- Format CSS and JavaScript (not HTML) with `prettier`.
- Preserve explanatory comments in Ruby code to keep the code approachable for non-Ruby developers.
  Add or update comments when changing logic, and do not remove existing comments unless they are obsolete.
