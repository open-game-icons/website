# Open Game Icons

An open source frontend to browse the free game icons from [Game-icons.net](https://www.game-icons.net).
For more about this project, see the [About](about/index.md) page.

## Setup

Build the database:

```sh
(cd assets/icons && ./rebuild_db.sh)
```

Serve the page:

```sh
bundle exec jekyll serve
```

## License

- Code: [AGPLv3](LICENSE.txt)
- Metadata: [CC0](METADATA_LICENSE.txt)
- Icons: see [assets/icons/license.txt](assets/icons/license.txt)
