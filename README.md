# Open Game Icons

An open source frontend to browse the free game icons from [Game-icons.net](https://www.game-icons.net).
For more about this project, see the [About](about/index.md) page.

## Setup

Build the database:

```sh
sqlite3 _db/icons.db < _db/icons.sql
```

Serve the page:

```sh
bundle exec jekyll serve
```
