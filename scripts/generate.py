#!/usr/bin/env python3
"""Generate Zola content and data from the icon SQLite database.

This replaces the jekyll-sqlite plugin and _plugins/data_mapper.rb. Zola has
no database plugin and no dynamic routes, so every icon and tag page needs a
small content stub. The stubs, lookup tables, route manifest, and client-side
search index are all derived from static/assets/icons/icons.db.

Run this before `zola build` whenever icons.sql changes.
"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "static/assets/icons/icons.db"
CONTENT_DIR = ROOT / "content/generated"
DATA_DIR = ROOT / "data/generated"
SEARCH_INDEX_PATH = ROOT / "static/search-index.json"

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
    tag_page_rows = connection.execute(TAG_PAGE_QUERY).fetchall()
    tag_info_rows = connection.execute(TAG_INFO_QUERY).fetchall()
    tag_icon_rows = connection.execute(TAG_ICONS_QUERY).fetchall()
    search_rows = connection.execute(SEARCH_QUERY).fetchall()
    connection.close()

    for row in icon_rows:
        if not SAFE_ID.match(row["author"]) or not SAFE_ID.match(row["icon_id"]):
            raise ValueError(f"unsafe icon id: {row['author']}/{row['icon_id']}")
    for row in tag_info_rows:
        if not SAFE_ID.match(row["id"]):
            raise ValueError(f"unsafe tag id: {row['id']}")

    # Ordered exactly like site.data.tag_info_array and its derived hashes.
    tag_info: dict[str, dict] = {}
    tag_ids: list[str] = []
    for row in tag_info_rows:
        tag_info[row["id"]] = {
            "name": row["name"],
            "count": row["count"],
            "parent": row["parent"],
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

    icons = [
        {
            "author": row["author"],
            "icon_id": row["icon_id"],
            "title": row["title"],
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
        tags = row["tags"].split(",") if row["tags"] else []
        filename = f"icon--{row['author']}--{row['icon_id']}.md"
        content = f"""+++
title = {toml_string(row["title"])}
template = "icon.html"
path = {toml_string(f"1x1/{row['author']}/{row['icon_id']}")}

[extra]
author = {toml_string(row["author"])}
icon_id = {toml_string(row["icon_id"])}
author_name = {toml_string(row["author_name"])}
author_link = {toml_string(row["author_link"] or "")}
license_name = {toml_string(row["license_name"])}
license_link = {toml_string(row["license_link"] or "")}
tags = {toml_array(tags)}
+++
"""
        (CONTENT_DIR / filename).write_text(content, encoding="utf-8")

    for row in tag_page_rows:
        content = f"""+++
title = {toml_string(row["name"])}
template = "tag_page.html"
path = {toml_string(f"tags/{row['id']}")}

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
    write_json(DATA_DIR / "icons.json", icons)
    write_json(
        DATA_DIR / "routes.json",
        {
            "icons": [
                {"author": row["author"], "icon_id": row["icon_id"]}
                for row in icon_rows
            ],
            "tags": [row["id"] for row in tag_page_rows],
        },
    )

    SEARCH_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(SEARCH_INDEX_PATH, build_search_index(search_rows))

    print(
        f"Generated {len(icon_rows)} icon pages, {len(tag_page_rows)} tag pages, "
        f"and {len(search_rows)} search index entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
