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
    icon_count = connection.execute("SELECT count(*) FROM icons").fetchone()[0]
    tag_count = connection.execute(
        "SELECT count(*) FROM (SELECT t.id FROM tags t JOIN icon_tags it ON t.id = it.tag "
        "GROUP BY t.id HAVING count(*) > 1)"
    ).fetchone()[0]
    connection.close()

    failures: list[str] = []

    icons = list((PUBLIC / "1x1").glob("*/*.html"))
    tags = list((PUBLIC / "tags").glob("*.html"))
    if len(icons) != icon_count:
        failures.append(f"expected {icon_count} icon pages, found {len(icons)}")
    if len(tags) != tag_count:
        failures.append(f"expected {tag_count} tag pages, found {len(tags)}")

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
        f"Checks OK: {len(icons)} icon pages, {len(tags)} tag pages, "
        f"{len(search_index)} search entries, {checked} internal links."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
