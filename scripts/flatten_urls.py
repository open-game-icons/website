#!/usr/bin/env python3
"""Move generated Zola pages from pretty URLs to the site's legacy .html URLs.

Zola always writes a page to <path>/index.html, even when the path ends in
.html. The existing site (and Game-icons.net compatibility) uses paths like
/1x1/lorc/sword.html, so we move only the generated icon and tag pages after
the build. Static files, About, the home page, and 404 are left alone.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
ROUTES = ROOT / "data/generated/routes.json"


def move_page(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"expected generated page is missing: {source}")
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite: {destination}")
    shutil.move(source, destination)


def main() -> int:
    routes = json.loads(ROUTES.read_text(encoding="utf-8"))

    for icon in routes["icons"]:
        directory = PUBLIC / "1x1" / icon["author"] / icon["icon_id"]
        move_page(
            directory / "index.html", directory.parent / f"{icon['icon_id']}.html"
        )
        directory.rmdir()

    for tag in routes["tags"]:
        directory = PUBLIC / "tags" / tag
        move_page(directory / "index.html", PUBLIC / "tags" / f"{tag}.html")
        directory.rmdir()

    # Zola emits these by default; the Jekyll site did not.
    (PUBLIC / "robots.txt").unlink(missing_ok=True)
    (PUBLIC / "sitemap.xml").unlink(missing_ok=True)

    # Static copies include dotfiles; these are repository metadata, not site
    # content.
    (PUBLIC / "assets/icons/.gitrepo").unlink(missing_ok=True)
    (PUBLIC / "assets/icons/.gitignore").unlink(missing_ok=True)

    # Remove the now-empty author directories.
    for author_dir in (PUBLIC / "1x1").iterdir():
        if author_dir.is_dir() and not any(author_dir.iterdir()):
            author_dir.rmdir()

    print(
        f"Flattened {len(routes['icons'])} icon pages and "
        f"{len(routes['tags'])} tag pages to .html URLs."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, FileExistsError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
