# AGENTS.md

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

- Jekyll static site for browsing icons.
- Icon SVGs sourced from `assets/icons` submodule.
- Metadata sourced from `_data/icons.json`.
- `_plugins/icon_generator.rb` (core site logic) generates icon and tag pages at build time, each as a `Jekyll::PageWithoutAFile`.

## Conventions

- Preserve explanatory comments in Ruby code to keep the code approachable for non-Ruby developers.
  Add or update comments when changing logic, and do not remove existing comments unless they are obsolete.
