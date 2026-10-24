# Open Game Icons

An open source frontend to browse the free game icons from [Game-icons.net](https://www.game-icons.net).
For more about this project, see the [About](content/about.md) page.

## Setup

This site is built with [Zola](https://www.getzola.org/) 0.23.6 and uses [just](https://just.systems/) for convenience commands.

Rebuild the icon database, generate the icon/tag content, and build the site:

```sh
just build
```

Preview the built output with local URLs:

```sh
just serve
```

`just serve` builds with `http://127.0.0.1:8000` as the base URL, runs the post-build cleanup, and serves `public/` without live reload.
That keeps the legacy `.html` alias redirects pointing at the local server.
Use `just serve 8080` to choose another port.
`zola serve` is available for live template iteration.

Canonical pages use Zola's pretty URLs:

- `/1x1/{author}/{icon_id}/`
- `/tags/{tag_id}/`

The old `.html` paths remain valid as Zola aliases, so URLs copied from Game-icons.net still resolve.
These aliases are client-side redirects (JavaScript with a meta-refresh fallback), not HTTP 301s.

The build publishes only the icon SVGs and license files from the icon subrepo; the SQLite database, SQL dump, scripts, and docs are pruned from `public/`.

Other commands:

```sh
just fmt       # format code and Tera templates
just db        # regenerate database (static/assets/icons/icons.db)
just generate  # regenerate content, data, and the search index
just check     # build and validate pages, aliases, and internal links
just clean     # remove build output and generated source files
```

Formatting Tera templates with `just fmt` requires [dprint](https://dprint.dev/) and [uv](https://docs.astral.sh/uv/), which runs djLint via `uvx` (downloaded on first use).

## License

- Code: [AGPLv3](static/LICENSE.txt)
- Metadata: [CC0](static/assets/icons/METADATA_LICENSE.txt)
- Icons: see [static/assets/icons/license.txt](static/assets/icons/license.txt)
