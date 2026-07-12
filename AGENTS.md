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
- Data sourced from 2 submodules: `assets/icons` (SVGs) and `assets/icons-metadata` (categories and tags).
- Icon pages (of the form `/1x1/author-name/icon-name/`) generated at build time by `_plugins/icon_generator.rb`, which reads `assets/icons-metadata/list-categories.txt` and creates one `Jekyll::PageWithoutAFile` per unique icon.
- The index page iterates over `site.data.icons.categories`, populated by the plugin.
- Layout hierarchy: `default` > `page` > `icon`
