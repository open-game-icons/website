#!/usr/bin/env python3
"""One-shot script to convert _data/*.json into _data/icons.db."""

import json
import sqlite3
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent


def main():
    conn = sqlite3.connect(PROJECT / "_data" / "icons.db")
    conn.execute("PRAGMA foreign_keys = ON")

    create_schema(conn)
    load_authors(conn)
    lic_map = load_licenses(conn)
    load_icons(conn, lic_map)
    load_tags(conn)
    load_junction_tables(conn)
    create_indices(conn)
    conn.commit()
    conn.close()
    print("Done — _data/icons.db created.")


def create_schema(conn):
    conn.executescript(
        """
        CREATE TABLE authors (
            id   TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            link TEXT
        );

        CREATE TABLE licenses (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            link TEXT
        );

        CREATE TABLE tags (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            parent      TEXT REFERENCES tags(id),
            icon_author TEXT NOT NULL,
            icon_id     TEXT NOT NULL,
            FOREIGN KEY (icon_author, icon_id) REFERENCES icons(author, id)
        );

        CREATE TABLE icons (
            author  TEXT NOT NULL REFERENCES authors(id),
            id      TEXT NOT NULL,
            license INTEGER NOT NULL REFERENCES licenses(id),
            name    TEXT NOT NULL,
            PRIMARY KEY (author, id)
        );

        CREATE TABLE icon_tags (
            author TEXT NOT NULL,
            id     TEXT NOT NULL,
            tag    TEXT NOT NULL REFERENCES tags(id),
            PRIMARY KEY (author, id, tag),
            FOREIGN KEY (author, id) REFERENCES icons(author, id)
        );

        CREATE TABLE icon_keywords (
            author  TEXT NOT NULL,
            id      TEXT NOT NULL,
            keyword TEXT NOT NULL,
            PRIMARY KEY (author, id, keyword),
            FOREIGN KEY (author, id) REFERENCES icons(author, id)
        );

        CREATE VIEW tag_icon_counts AS
        SELECT t.id, t.name, count(it.author) AS count
        FROM tags t
        LEFT JOIN icon_tags it ON t.id = it.tag
        GROUP BY t.id;
        """
    )


def create_indices(conn):
    conn.executescript(
        """
        CREATE INDEX idx_icon_tags_tag ON icon_tags(tag);
        CREATE INDEX idx_icon_tags_icon ON icon_tags(author, id);
        CREATE INDEX idx_icon_keywords_icon ON icon_keywords(author, id);
        """
    )


def load_authors(conn):
    with open(PROJECT / "_data" / "authors.json") as f:
        authors = json.load(f)
    conn.executemany(
        "INSERT INTO authors (id, name, link) VALUES (?, ?, ?)",
        ((aid, a.get("name", aid), a.get("link")) for aid, a in authors.items()),
    )
    print(f"  Loaded {len(authors)} authors")


def load_licenses(conn):
    with open(PROJECT / "_data" / "licenses.json") as f:
        licenses = json.load(f)
    mapping = {}
    for lid, info in licenses.items():
        cur = conn.execute(
            "INSERT INTO licenses (name, link) VALUES (?, ?) RETURNING id",
            (info["name"], info["link"]),
        )
        mapping[lid] = cur.fetchone()[0]
    print(f"  Loaded {len(licenses)} licenses (ids: {mapping})")
    return mapping


def load_icons(conn, lic_map):
    with open(PROJECT / "_data" / "icons.json") as f:
        icons = json.load(f)

    conn.executemany(
        "INSERT INTO icons (author, id, license, name) VALUES (?, ?, ?, ?)",
        (
            (info["author"], info["id"], lic_map[info["license"]], info["name"])
            for info in icons.values()
        ),
    )
    print(f"  Loaded {len(icons)} icons")


def load_tags(conn):
    with open(PROJECT / "_data" / "tags.json") as f:
        tags = json.load(f)

    conn.executemany(
        "INSERT INTO tags (id, name, parent, icon_author, icon_id) VALUES (?, ?, ?, ?, ?)",
        (
            (slug, t["name"], t.get("parent"), t["icon_author"], t["icon"])
            for slug, t in tags.items()
        ),
    )
    print(f"  Loaded {len(tags)} tags")


def load_junction_tables(conn):
    with open(PROJECT / "_data" / "icons.json") as f:
        icons = json.load(f)

    tag_rows = []
    keyword_rows = []

    for info in icons.values():
        author = info["author"]
        icon_id = info["id"]
        for tag in info.get("tags", []):
            tag_rows.append((author, icon_id, tag))
        for kw in info.get("keywords", []):
            keyword_rows.append((author, icon_id, kw))

    conn.executemany(
        "INSERT INTO icon_tags (author, id, tag) VALUES (?, ?, ?)", tag_rows
    )
    conn.executemany(
        "INSERT INTO icon_keywords (author, id, keyword) VALUES (?, ?, ?)",
        keyword_rows,
    )
    print(f"  Loaded {len(tag_rows)} icon-tag associations")
    print(f"  Loaded {len(keyword_rows)} icon-keyword associations")


if __name__ == "__main__":
    main()
