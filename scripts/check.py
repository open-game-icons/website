#!/usr/bin/env python3
"""Validate the built site: expected pages and resolvable internal links."""

from __future__ import annotations

import json
import sqlite3
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
DB_PATH = ROOT / "static/assets/icons/icons.db"
ICON_ASSETS = PUBLIC / "assets/icons"
PUBLISHED_ICON_FILES = {"license.txt", "METADATA_LICENSE.txt"}


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.links.append(value)


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
    tag_rows = connection.execute(
        "SELECT t.id FROM tags t JOIN icon_tags it ON t.id = it.tag "
        "GROUP BY t.id HAVING count(*) > 1"
    ).fetchall()
    connection.close()
    icon_count = len(icon_rows)
    tag_count = len(tag_rows)

    failures: list[str] = []

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
                failures.append(f"missing published icon file: assets/icons/{entry}")

        for entry in ICON_ASSETS.iterdir():
            if entry.is_symlink() or (
                entry.is_file() and entry.name not in PUBLISHED_ICON_FILES
            ):
                failures.append(
                    f"build-only asset published: assets/icons/{entry.name}"
                )
            elif entry.is_dir() and entry.name.startswith((".", "_")):
                failures.append(
                    f"build-only asset published: assets/icons/{entry.name}/"
                )

    icons = list((PUBLIC / "1x1").glob("*/*/index.html"))
    tags = list((PUBLIC / "tags").glob("*/index.html"))
    if len(icons) != icon_count:
        failures.append(f"expected {icon_count} icon pages, found {len(icons)}")
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
        f"{len(tags)} tag pages (+ aliases), "
        f"{len(search_index)} search entries, {checked} internal links."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
