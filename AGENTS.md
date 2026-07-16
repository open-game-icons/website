# AGENTS.md

Jekyll static site for browsing icons.

## Setup

```sh
git submodule update --init --recursive
bundle install
```

## Build

```sh
bundle exec jekyll build
```

## Architecture

- `assets/icons`: submodule containing icon SVGs
- `_data/icons.json`: metadata
- `_plugins/icon_generator.rb`: core site generator logic
	- Generates icon and tag pages at build time, each as a `Jekyll::PageWithoutAFile`
	- Populates data `search-index.json`
- `assets/js/search.js`: client-side search

## Conventions

- Format CSS and JavaScript (not HTML) with `prettier`.
- Preserve explanatory comments in Ruby code to keep the code approachable for non-Ruby developers.
  Add or update comments when changing logic, and do not remove existing comments unless they are obsolete.
