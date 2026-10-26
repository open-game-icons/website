#!/usr/bin/env python3
"""Validate the built site: expected pages, homepage visibility, and links."""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from generate import creative_commons_icon_urls

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
DB_PATH = ROOT / "icons/icons.db"
ICON_ASSETS = PUBLIC / "icons"
PUBLISHED_ICON_FILES = {"license.txt", "METADATA_LICENSE.txt"}

# Bundled from src/ts by Bun and copied by Zola.
COMPILED_JS = ("search.js", "icon-download.js", "build-time.js")

# DOM hooks used by src/ts/icon-download.ts. TypeScript cannot verify Tera
# template output, so these checks guard the template contract.
REQUIRED_ICON_PAGE_IDS = {
    "downloads",
    "svg-download",
    "png-download",
    "png-download-controls",
    "download-size",
}
REQUIRED_ICON_PAGE_DATA_ATTRIBUTES = {
    "data-icon-title",
    "data-icon-id",
    "data-file-base",
    "data-author",
    "data-license-name",
    "data-license-url",
    "data-source-url",
    "data-attribution",
}

# Download filenames are built as "{icon}-{author}-{license}", so each component
# must be filename-safe. Underscores are deliberately disallowed so one can be
# used as a field delimiter later.
FILENAME_COMPONENT = re.compile(r"^[a-z0-9][a-z0-9.-]*$")


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.links.append(value)


class HomepageVisibilityParser(HTMLParser):
    """Collect homepage icon ids and links marked hidden on the homepage."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.icon_ids: list[str] = []
        self.hidden_icons: list[str] = []
        self.hidden_tags: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return

        attributes = dict(attrs)
        icon_id = attributes.get("id", "")
        if icon_id.startswith("icon--"):
            self.icon_ids.append(icon_id)

        if "data-homepage-hidden" not in attributes:
            return

        href = attributes.get("href", "")
        if href.startswith("/tags/"):
            self.hidden_tags.append(href.removeprefix("/tags/").strip("/"))
        elif href.startswith("/1x1/"):
            self.hidden_icons.append(href)


class IconPageContractParser(HTMLParser):
    """Collect ids and data attributes used by the icon studio."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.data_attributes: set[str] = set()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.ids.add(element_id)
        for name, _ in attrs:
            if name.startswith("data-"):
                self.data_attributes.add(name)


def resolve(page: Path, link: str) -> Path | None:
    """Return the output file a link should resolve to, or None to skip it."""
    if link.startswith(
        ("http://", "https://", "mailto:", "tel:", "data:", "javascript:")
    ):
        return None

    parts = urlsplit(link)
    path = unquote(parts.path)
    if not path:
        return None

    if path.startswith("/"):
        target = PUBLIC / path.lstrip("/")
    else:
        target = page.parent / path

    if target.is_dir():
        target = target / "index.html"
    elif not target.exists() and (target.with_name(target.name + ".html")).exists():
        target = target.with_name(target.name + ".html")

    return target


def main() -> int:
    if not PUBLIC.is_dir():
        print("error: public/ is missing; run `just build` first", file=sys.stderr)
        return 1

    connection = sqlite3.connect(DB_PATH)
    icon_rows = connection.execute("SELECT author, id FROM icons").fetchall()
    license_rows = connection.execute(
        "SELECT l.id, i.author, i.id FROM licenses l "
        "JOIN icons i ON i.license = l.id "
        "ORDER BY l.id, i.author, i.id"
    ).fetchall()
    author_rows = connection.execute("SELECT id FROM authors").fetchall()
    license_ids = [
        row[0] for row in connection.execute("SELECT id FROM licenses ORDER BY id")
    ]
    tag_rows = connection.execute(
        "SELECT t.id FROM tags t JOIN icon_tags it ON t.id = it.tag "
        "GROUP BY t.id HAVING count(*) > 1"
    ).fetchall()
    connection.close()
    icon_count = len(icon_rows)
    author_count = len(author_rows)
    tag_count = len(tag_rows)

    failures: list[str] = []

    for license_id in license_ids:
        if not FILENAME_COMPONENT.match(license_id):
            failures.append(f"license id is not filename-safe: {license_id!r}")

    if not ICON_ASSETS.is_dir():
        failures.append(
            f"icon output directory is missing: {ICON_ASSETS.relative_to(ROOT)}"
        )
    else:
        for author, icon_id in icon_rows:
            if not (ICON_ASSETS / author / f"{icon_id}.svg").is_file():
                failures.append(f"missing icon SVG: {author}/{icon_id}.svg")

        for entry in PUBLISHED_ICON_FILES:
            if not (ICON_ASSETS / entry).is_file():
                failures.append(f"missing published icon file: icons/{entry}")

        for entry in ICON_ASSETS.iterdir():
            if entry.is_symlink() or (
                entry.is_file() and entry.name not in PUBLISHED_ICON_FILES
            ):
                failures.append(f"build-only asset published: icons/{entry.name}")
            elif entry.is_dir() and entry.name.startswith((".", "_")):
                failures.append(f"build-only asset published: icons/{entry.name}/")

    js_assets = PUBLIC / "js"
    for filename in COMPILED_JS:
        script = js_assets / filename
        if not script.is_file():
            failures.append(f"missing compiled script: js/{filename}")
        elif script.stat().st_size == 0:
            failures.append(f"empty compiled script: js/{filename}")

    for pattern in ("*.ts", "*.tsx"):
        for source in PUBLIC.rglob(pattern):
            failures.append(
                f"TypeScript source published: {source.relative_to(PUBLIC)}"
            )

    icons = list((PUBLIC / "1x1").glob("*/*/index.html"))
    author_pages = list((PUBLIC / "1x1").glob("*/index.html"))
    tags = list((PUBLIC / "tags").glob("*/index.html"))
    if len(icons) != icon_count:
        failures.append(f"expected {icon_count} icon pages, found {len(icons)}")
    if len(author_pages) != author_count:
        failures.append(
            f"expected {author_count} author pages, found {len(author_pages)}"
        )
    if len(tags) != tag_count:
        failures.append(f"expected {tag_count} tag pages, found {len(tags)}")

    # Every generated page should also have a legacy .html alias pointing at
    # its canonical pretty URL.
    for author, icon_id in icon_rows:
        canonical = PUBLIC / "1x1" / author / icon_id / "index.html"
        alias = PUBLIC / "1x1" / author / f"{icon_id}.html"
        if not canonical.is_file():
            failures.append(f"missing icon page: 1x1/{author}/{icon_id}/")
        if not alias.is_file():
            failures.append(f"missing icon alias: 1x1/{author}/{icon_id}.html")
        elif f"/1x1/{author}/{icon_id}/" not in alias.read_text(encoding="utf-8"):
            failures.append(f"icon alias does not point to canonical URL: {alias}")

    for (author,) in author_rows:
        canonical = PUBLIC / "1x1" / author / "index.html"
        if not canonical.is_file():
            failures.append(f"missing author page: 1x1/{author}/")

    for (tag_id,) in tag_rows:
        canonical = PUBLIC / "tags" / tag_id / "index.html"
        alias = PUBLIC / "tags" / f"{tag_id}.html"
        if not canonical.is_file():
            failures.append(f"missing tag page: tags/{tag_id}/")
        if not alias.is_file():
            failures.append(f"missing tag alias: tags/{tag_id}.html")
        elif f"/tags/{tag_id}/" not in alias.read_text(encoding="utf-8"):
            failures.append(f"tag alias does not point to canonical URL: {alias}")

    search_index = json.loads(
        (PUBLIC / "search-index.json").read_text(encoding="utf-8")
    )
    if len(search_index) != icon_count:
        failures.append(
            f"expected {icon_count} search entries, found {len(search_index)}"
        )

    homepage_icons = json.loads(
        (ROOT / "data/generated/icons.json").read_text(encoding="utf-8")
    )
    hidden_icons = {
        f"/1x1/{icon['author']}/{icon['icon_id']}/"
        for icon in homepage_icons
        if icon.get("hidden_on_homepage")
    }
    tag_info = json.loads(
        (ROOT / "data/generated/tag_info.json").read_text(encoding="utf-8")
    )
    hidden_tags = {tag_id for tag_id, info in tag_info.items() if info.get("parent")}

    homepage = (PUBLIC / "index.html").read_text(encoding="utf-8")
    homepage_parser = HomepageVisibilityParser()
    homepage_parser.feed(homepage)

    homepage_icon_ids = set(homepage_parser.icon_ids)
    search_keys = set(search_index)
    if homepage_icon_ids != search_keys:
        missing = sorted(search_keys - homepage_icon_ids)[:5]
        extra = sorted(homepage_icon_ids - search_keys)[:5]
        failures.append(
            "search index keys do not match homepage icon ids "
            f"(missing={missing}, extra={extra})"
        )

    if set(homepage_parser.hidden_icons) != hidden_icons:
        failures.append(
            f"expected {len(hidden_icons)} homepage-hidden icons, "
            f"found {len(set(homepage_parser.hidden_icons))}"
        )
    if set(homepage_parser.hidden_tags) != hidden_tags:
        failures.append(
            f"expected {len(hidden_tags)} homepage-hidden tags, "
            f"found {len(set(homepage_parser.hidden_tags))}"
        )

    for page in (PUBLIC / "tags").glob("*/index.html"):
        if "data-homepage-hidden" in page.read_text(encoding="utf-8"):
            failures.append(
                f"tag page contains homepage-hidden items: {page.relative_to(PUBLIC)}"
            )

    # The license marks are the same for every icon under a license, so one
    # page per license is enough to validate the generated front matter.
    license_samples: dict[str, tuple[str, str]] = {}
    for license_id, author, icon_id in license_rows:
        license_samples.setdefault(license_id, (author, icon_id))

    for license_id, (author, icon_id) in license_samples.items():
        page = PUBLIC / "1x1" / author / icon_id / "index.html"
        html = page.read_text(encoding="utf-8")
        for icon_url in creative_commons_icon_urls(license_id):
            if f'src="{icon_url}"' not in html:
                failures.append(
                    f"missing license icon on 1x1/{author}/{icon_id}/: {icon_url}"
                )

    if icon_rows:
        author, icon_id = icon_rows[0]
        icon_page = PUBLIC / "1x1" / author / icon_id / "index.html"
        if icon_page.is_file():
            contract_parser = IconPageContractParser()
            contract_parser.feed(icon_page.read_text(encoding="utf-8"))
            missing_ids = REQUIRED_ICON_PAGE_IDS - contract_parser.ids
            missing_data = (
                REQUIRED_ICON_PAGE_DATA_ATTRIBUTES - contract_parser.data_attributes
            )
            if missing_ids:
                failures.append(
                    f"icon page is missing studio ids: {sorted(missing_ids)}"
                )
            if missing_data:
                failures.append(
                    "icon page is missing studio data attributes: "
                    f"{sorted(missing_data)}"
                )

    checked = 0
    for page in sorted(PUBLIC.rglob("*.html")):
        parser = LinkParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for link in parser.links:
            target = resolve(page, link)
            if target is None:
                continue
            checked += 1
            if not target.exists():
                failures.append(f"{page.relative_to(PUBLIC)}: broken link {link!r}")

    if failures:
        print("\n".join(f"FAIL: {failure}" for failure in failures[:50]))
        print(f"\n{len(failures)} check(s) failed")
        return 1

    print(
        f"Checks OK: {len(icons)} icon pages (+ aliases), "
        f"{len(author_pages)} author pages, "
        f"{len(tags)} tag pages (+ aliases), "
        f"{len(search_index)} search entries, {checked} internal links."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
