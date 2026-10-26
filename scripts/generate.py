#!/usr/bin/env python3
"""Generate Zola content and data from the icon SQLite database.

This replaces the jekyll-sqlite plugin and _plugins/data_mapper.rb. Zola has
no database plugin and no dynamic routes, so every icon, author, and tag page
needs a small content stub. The stubs, lookup tables, and client-side search
index are all derived from icons/icons.db. Each icon and tag stub also declares
the legacy .html path as a Zola alias, which produces the redirect files used
by incoming Game-icons.net-compatible URLs.

The publish-only static view of the icon subrepo is regenerated here too:
static/icons contains symlinks to the SVG directories and license files,
so Zola never sees the database, SQL dump, scripts, or docs.

Run this before `zola build` whenever icons.sql changes.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = ROOT / "icons"
STATIC_ICONS_DIR = ROOT / "static/icons"
DB_PATH = ICONS_DIR / "icons.db"
CONTENT_DIR = ROOT / "content/generated"
DATA_DIR = ROOT / "data/generated"
SEARCH_INDEX_PATH = ROOT / "static/search-index.json"
PUBLISHED_ICON_FILES = {"license.txt", "METADATA_LICENSE.txt"}


class AuthorEntry(TypedDict):
    id: str
    name: str
    link: str
    icon_count: int


# These queries mirror _config.yml. Keep the lack of ORDER BY where the
# original query had none: the generated output currently preserves SQLite's
# row order, and changing it would change the order of tag links on pages.
ICON_QUERY = """
  SELECT
    i.author AS author,
    i.id     AS icon_id,
    i.name   AS title,
    a.name   AS author_name,
    a.link   AS author_link,
    l.id     AS license_id,
    l.name   AS license_name,
    l.link   AS license_link,
    group_concat(DISTINCT it.tag) AS tags
  FROM icons i
  JOIN authors  a ON i.author  = a.id
  JOIN licenses l ON i.license = l.id
  LEFT JOIN icon_tags it ON i.author = it.author AND i.id = it.id
  GROUP BY i.author, i.id
  ORDER BY i.name, i.id
"""

AUTHOR_QUERY = """
  SELECT
    a.id,
    a.name,
    a.link
  FROM authors a
"""

TAG_PAGE_QUERY = """
  SELECT
    t.id   AS id,
    t.name AS name
  FROM tags t
  JOIN icon_tags it ON t.id = it.tag
  GROUP BY t.id
  HAVING count(*) > 1
"""

TAG_INFO_QUERY = """
  SELECT
    t.id,
    t.name,
    t.parent,
    t.icon_author,
    t.icon_id,
    count(it.tag) AS count
  FROM tags t
  LEFT JOIN icon_tags it ON t.id = it.tag
  GROUP BY t.id
"""

TAG_ICONS_QUERY = """
  SELECT
    it.tag,
    i.author,
    i.id AS icon_id,
    i.name AS title
  FROM icon_tags it
  JOIN icons i ON it.author = i.author AND it.id = i.id
  ORDER BY i.name, i.id
"""

SEARCH_QUERY = """
  SELECT
    i.author,
    i.id,
    i.name,
    group_concat(DISTINCT it.tag)     AS tag_list,
    group_concat(DISTINCT ik.keyword) AS keyword_list
  FROM icons i
  LEFT JOIN icon_tags     it ON i.author = it.author AND i.id = it.id
  LEFT JOIN icon_keywords ik ON i.author = ik.author AND i.id = ik.id
  GROUP BY i.author, i.id
"""

# Author ids, icon ids, and tag ids are all slugs. Asserting that keeps the
# generated file names and output paths safe and predictable.
SAFE_ID = re.compile(r"^[a-z0-9-]+$")

# Creative Commons' trademark policy requires marks downloaded directly from
# creativecommons.org, so point at its press-kit mirror instead of bundling
# copies. Element marks are ordered the way the press kit presents them.
CC_ICON_URL = "https://mirrors.creativecommons.org/presskit/icons/{name}.svg"
CC_LICENSE_ID = re.compile(
    r"^cc-(?P<elements>(?:by|nc|nd|sa)(?:-(?:by|nc|nd|sa))*)-[0-9.]+(?:-[a-z]{2})?$"
)
CC_LICENSE_ELEMENT_ORDER = ("by", "nc", "nd", "sa")


def creative_commons_icon_urls(license_id: str) -> list[str]:
    """Map a Creative Commons license id to its official press-kit icons.

    CC0 uses the CC and Zero marks. Other CC licenses use the CC mark followed
    by their element marks (BY, NC, ND, SA). Non-CC license ids get no icons.
    """
    if license_id == "cc0":
        names = ["cc", "zero"]
    else:
        match = CC_LICENSE_ID.match(license_id)
        if not match:
            return []
        elements = set(match.group("elements").split("-"))
        names = ["cc", *(e for e in CC_LICENSE_ELEMENT_ORDER if e in elements)]

    return [CC_ICON_URL.format(name=name) for name in names]


# Icons with any of these tags are hidden from the homepage grid by default.
# They still appear when a search matches, on tag pages, and via direct links.
HOMEPAGE_HIDDEN_ICON_TAGS = [
    "abstract",
    "alchemical-symbol",
    "dice",
    "elder-futhark",
    "playing-card",
    "tarot",
]


def toml_string(value: str) -> str:
    """Return a TOML basic string, reusing JSON's compatible escaping."""
    return json.dumps(value, ensure_ascii=False)


def toml_array(values: list[str]) -> str:
    return "[" + ", ".join(toml_string(value) for value in values) + "]"


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))


def slugify(value: str) -> str:
    """Approximate Jekyll::Utils.slugify's default mode.

    The current tag ids are already slugs, so this is mostly a safety net if
    a non-slug tag id is added later.
    """
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def build_search_index(rows: list[sqlite3.Row]) -> dict[str, list[str]]:
    """Port of DataMapper#map_search_index from _plugins/data_mapper.rb."""
    lookup: dict[str, list[str]] = {}

    for row in rows:
        icon_name = row["name"] or row["id"]
        words = row["id"].split("-")
        words.extend(icon_name.lower().split())

        if row["tag_list"]:
            for tag in row["tag_list"].split(","):
                words.extend(slugify(tag).split("-"))

        if row["keyword_list"]:
            for keyword in row["keyword_list"].split(","):
                words.extend(keyword.lower().split())

        key = f"icon--{row['author']}--{row['id']}"
        lookup[key] = sorted(set(words))

    return lookup


def stage_static_icons() -> int:
    """Create the publish-only static view of the icon subrepo.

    Zola copies everything under static/, so stage symlinks only for the
    author/badge SVG directories and license files. Zola follows symlinks and
    writes regular files into public/, which also keeps `zola serve` accurate
    without a post-build pruning step.
    """
    if STATIC_ICONS_DIR.is_symlink() or STATIC_ICONS_DIR.is_file():
        STATIC_ICONS_DIR.unlink()
    elif STATIC_ICONS_DIR.exists():
        shutil.rmtree(STATIC_ICONS_DIR)
    STATIC_ICONS_DIR.mkdir(parents=True)

    staged = 0
    for entry in sorted(ICONS_DIR.iterdir()):
        if entry.is_dir():
            if entry.name.startswith((".", "_")):
                continue
        elif entry.name not in PUBLISHED_ICON_FILES:
            continue

        target = os.path.relpath(entry, STATIC_ICONS_DIR)
        (STATIC_ICONS_DIR / entry.name).symlink_to(
            target, target_is_directory=entry.is_dir()
        )
        staged += 1

    return staged


def main() -> int:
    if not DB_PATH.exists():
        print(
            f"error: {DB_PATH} is missing; run `just db`",
            file=sys.stderr,
        )
        return 1

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    icon_rows = connection.execute(ICON_QUERY).fetchall()
    author_rows = connection.execute(AUTHOR_QUERY).fetchall()
    tag_page_rows = connection.execute(TAG_PAGE_QUERY).fetchall()
    tag_info_rows = connection.execute(TAG_INFO_QUERY).fetchall()
    tag_icon_rows = connection.execute(TAG_ICONS_QUERY).fetchall()
    search_rows = connection.execute(SEARCH_QUERY).fetchall()
    connection.close()

    for row in icon_rows:
        if not SAFE_ID.match(row["author"]) or not SAFE_ID.match(row["icon_id"]):
            raise ValueError(f"unsafe icon id: {row['author']}/{row['icon_id']}")
    for row in author_rows:
        if not SAFE_ID.match(row["id"]):
            raise ValueError(f"unsafe author id: {row['id']}")
    for row in tag_info_rows:
        if not SAFE_ID.match(row["id"]):
            raise ValueError(f"unsafe tag id: {row['id']}")
    known_tags = {row["id"] for row in tag_info_rows}
    for tag in sorted(HOMEPAGE_HIDDEN_ICON_TAGS):
        if not SAFE_ID.match(tag):
            raise ValueError(f"unsafe hidden homepage tag id: {tag}")
        if tag not in known_tags:
            raise ValueError(f"HOMEPAGE_HIDDEN_ICON_TAGS references unknown tag: {tag}")

    # Ordered exactly like site.data.tag_info_array and its derived hashes.
    tag_info: dict[str, dict] = {}
    tag_ids: list[str] = []
    for row in tag_info_rows:
        tag_info[row["id"]] = {
            "name": row["name"],
            "count": row["count"],
            "parent": row["parent"],
            "icon_author": row["icon_author"],
            "icon_id": row["icon_id"],
        }
        tag_ids.append(row["id"])

    # Related tags are the tag's children in tag_info order, followed by its
    # parent. This matches _layouts/tag_page.html's Liquid logic.
    related_tags: dict[str, list[str]] = {row["id"]: [] for row in tag_page_rows}
    for row in tag_page_rows:
        tag_id = row["id"]
        related_tags[tag_id] = [
            candidate["id"]
            for candidate in tag_info_rows
            if candidate["parent"] == tag_id
        ]
        parent = tag_info[tag_id]["parent"]
        if parent:
            related_tags[tag_id].append(parent)

    tag_icons: dict[str, list[dict]] = {}
    for row in tag_icon_rows:
        tag_icons.setdefault(row["tag"], []).append(
            {
                "author": row["author"],
                "icon_id": row["icon_id"],
                "title": row["title"],
            }
        )

    author_icons: dict[str, list[dict]] = {row["id"]: [] for row in author_rows}
    for row in icon_rows:
        author_icons[row["author"]].append(
            {
                "author": row["author"],
                "icon_id": row["icon_id"],
                "title": row["title"],
            }
        )

    icon_tags: dict[tuple[str, str], list[str]] = {
        (row["author"], row["icon_id"]): (row["tags"].split(",") if row["tags"] else [])
        for row in icon_rows
    }

    icons = [
        {
            "author": row["author"],
            "icon_id": row["icon_id"],
            "title": row["title"],
            "hidden_on_homepage": bool(
                set(HOMEPAGE_HIDDEN_ICON_TAGS).intersection(
                    icon_tags[(row["author"], row["icon_id"])]
                )
            ),
        }
        for row in icon_rows
    ]

    # Rebuild generated directories from scratch so removed DB rows cannot
    # leave stale pages behind.
    if CONTENT_DIR.exists():
        shutil.rmtree(CONTENT_DIR)
    CONTENT_DIR.mkdir(parents=True)

    # An explicit section with render = false avoids orphan-page warnings
    # without publishing an extra /generated/ route.
    (CONTENT_DIR / "_index.md").write_text(
        '+++\ntitle = "Generated"\nrender = false\n+++\n', encoding="utf-8"
    )

    for row in icon_rows:
        tags = icon_tags[(row["author"], row["icon_id"])]
        filename = f"icon--{row['author']}--{row['icon_id']}.md"
        content = f"""+++
title = {toml_string(row["title"])}
template = "icon.html"
path = {toml_string(f"1x1/{row['author']}/{row['icon_id']}")}
aliases = {toml_array([f"/1x1/{row['author']}/{row['icon_id']}.html"])}

[extra]
author = {toml_string(row["author"])}
icon_id = {toml_string(row["icon_id"])}
author_name = {toml_string(row["author_name"])}
author_link = {toml_string(row["author_link"] or "")}
license_id = {toml_string(row["license_id"])}
license_name = {toml_string(row["license_name"])}
license_link = {toml_string(row["license_link"] or "")}
license_icons = {toml_array(creative_commons_icon_urls(row["license_id"]))}
tags = {toml_array(tags)}
+++
"""
        (CONTENT_DIR / filename).write_text(content, encoding="utf-8")

    for row in author_rows:
        content = f"""+++
title = {toml_string(row["name"])}
template = "author_page.html"
path = {toml_string(f"1x1/{row['id']}")}

[extra]
slug = {toml_string(row["id"])}
list_name = {toml_string(row["name"])}
author_link = {toml_string(row["link"] or "")}
+++
"""
        (CONTENT_DIR / f"author--{row['id']}.md").write_text(content, encoding="utf-8")

    for row in tag_page_rows:
        content = f"""+++
title = {toml_string(row["name"])}
template = "tag_page.html"
path = {toml_string(f"tags/{row['id']}")}
aliases = {toml_array([f"/tags/{row['id']}.html"])}

[extra]
slug = {toml_string(row["id"])}
list_name = {toml_string(row["name"])}
related_tags = {toml_array(related_tags[row["id"]])}
+++
"""
        (CONTENT_DIR / f"tag--{row['id']}.md").write_text(content, encoding="utf-8")

    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(parents=True)

    write_json(DATA_DIR / "tag_info.json", tag_info)
    write_json(DATA_DIR / "tag_ids.json", tag_ids)
    write_json(DATA_DIR / "tag_icons.json", tag_icons)
    write_json(DATA_DIR / "author_icons.json", author_icons)
    write_json(DATA_DIR / "icons.json", icons)
    write_json(
        DATA_DIR / "stats.json",
        {
            "icon_count": len(icon_rows),
            "author_count": len(author_rows),
            "tag_count": len(tag_info_rows),
        },
    )

    authors: list[AuthorEntry] = [
        {
            "id": row["id"],
            "name": row["name"] or row["id"],
            "link": row["link"] or "",
            "icon_count": len(author_icons[row["id"]]),
        }
        for row in author_rows
    ]
    authors.sort(
        key=lambda author: (
            -author["icon_count"],
            author["name"].casefold(),
            author["id"],
        )
    )
    write_json(DATA_DIR / "authors.json", authors)

    tag_children: dict[str, list[dict]] = {row["id"]: [] for row in tag_info_rows}
    for row in tag_info_rows:
        if row["parent"]:
            tag_children[row["parent"]].append({"id": row["id"], "name": row["name"]})
    tag_tree = [
        {
            "id": row["id"],
            "name": row["name"],
            "children": tag_children[row["id"]],
        }
        for row in tag_info_rows
        if not row["parent"]
    ]
    write_json(DATA_DIR / "tag_tree.json", tag_tree)

    SEARCH_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(SEARCH_INDEX_PATH, build_search_index(search_rows))

    staged = stage_static_icons()

    print(
        f"Generated {len(icon_rows)} icon pages, {len(author_rows)} author pages, "
        f"{len(tag_page_rows)} tag pages, {len(search_rows)} search index entries, "
        f"and {staged} staged icon asset entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
