# Open Game Icons

An open source frontend to browse the free game icons from [Game-icons.net](https://www.game-icons.net).
For more about this project, see the [About](content/about.md) page.

## Setup

This site is built with [Zola](https://www.getzola.org/) 0.23.6 and uses [just](https://just.systems/) for convenience commands.

Build the database (rerun this whenever `static/assets/icons/icons.sql` changes):

```sh
just db
```

Generate the icon/tag content and build the site:

```sh
just build
```

Preview the actual built output:

```sh
just serve
```

The build publishes only the icon SVGs and `license.txt` from the icon subrepo; the SQLite database, SQL dump, scripts, and docs are pruned from `public/`.

`just serve` builds `public/` and serves it without live reload.
`zola serve` can be used while iterating on templates, but it uses Zola's pretty URL layout; the site's public `.html` URLs only exist after `scripts/post_build.py` runs.

Other commands:

```sh
just generate  # regenerate content, data, and the search index
just check     # build and validate page counts and internal links
just clean     # remove build output and generated source files
```

## License

- Code: [AGPLv3](static/LICENSE.txt)
- Metadata: [CC0](static/assets/icons/METADATA_LICENSE.txt)
- Icons: see [static/assets/icons/license.txt](static/assets/icons/license.txt)
