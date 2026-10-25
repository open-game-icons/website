# Open Game Icons

An open source frontend to browse the free game icons from [Game-icons.net](https://www.game-icons.net).
For more about this project, see the [About](content/about.md) page.

## Setup

This site is built with [Zola](https://www.getzola.org/) 0.23.6 with additional generator scripts that require Python 3.11+.
[just](https://just.systems/) is used as a command runner for convenience.

Rebuild the icon database, generate the icon, author, and tag content, and build the site:

```sh
just build
```

Serve locally with live reload:

```sh
just serve
```

`just serve` runs `zola serve` on port 8000 after regenerating the content and static assets.
Zola uses its local server URL as the base URL, so legacy `.html` alias redirects stay local.
Use `just serve 8080` to choose another port.

Canonical pages use Zola's pretty URLs:

- `/1x1/{author}/{icon_id}/`
- `/1x1/{author}/`
- `/tags/{tag_id}/`

The old `.html` paths remain valid as Zola aliases, so URLs copied from Game-icons.net still resolve.
These aliases are client-side redirects (JavaScript with a meta-refresh fallback), not HTTP 301s.

The generator symlinks only the icon SVG directories and license files from `icons/` into `static/assets/icons`; the SQLite database, SQL dump, scripts, and docs are never published.

Other commands:

```sh
just fmt       # format code and Tera templates
just db        # regenerate database (icons/icons.db)
just generate  # regenerate content, data, search index, and static icon staging
just check     # build and validate pages, aliases, and internal links
just clean     # remove build output and generated source files
```

Formatting Tera templates with `just fmt` requires [dprint](https://dprint.dev/) and [uv](https://docs.astral.sh/uv/), which runs djLint via `uvx` (downloaded on first use).

## License

- Code: [AGPLv3](static/LICENSE.txt)
- Metadata: [CC0](icons/METADATA_LICENSE.txt)
- Icons: see [icons/license.txt](icons/license.txt)
