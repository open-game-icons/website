# Open Game Icons

An open source frontend to browse the [free game icons](https://github.com/game-icons/icons) from [game-icons.net](https://www.game-icons.net).

## Setup

Build the database:

```sh
sqlite3 _db/icons.db < _db/icons.sql
```

Serve the page:

```sh
bundle exec jekyll serve
```
