#!/usr/bin/env python3
"""Post-process the Zola build.

Zola always writes a page to <path>/index.html, even when the path ends in
.html. The existing site (and Game-icons.net compatibility) uses paths like
/1x1/lorc/sword.html, so we move only the generated icon and tag pages after
the build. Static files, About, the home page, and 404 are left alone.

Zola also copies the entire icon subrepo from static/assets/icons. Only the
SVG directories and license.txt belong on the site, so the database, SQL,
scripts, and docs are pruned from the output here.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
ROUTES = ROOT / "data/generated/routes.json"
ICONS = PUBLIC / "assets/icons"
PUBLISHED_ICON_FILES = {"license.txt"}


def move_page(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"expected generated page is missing: {source}")
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite: {destination}")
    shutil.move(source, destination)


def prune_icon_helpers() -> tuple[int, int]:
    """Remove build-only files copied from static/assets/icons.

    Keep the author/badge SVG directories and license.txt. Everything else at
    the top level is a database, SQL dump, script, or documentation file that
    does not belong on the site.
    """
    if not ICONS.is_dir():
        raise FileNotFoundError(f"expected icon output directory is missing: {ICONS}")

    removed = 0
    removed_bytes = 0

    for entry in ICONS.iterdir():
        if entry.is_symlink():
            removed_bytes += entry.lstat().st_size
            entry.unlink()
            removed += 1
        elif entry.is_dir():
            if entry.name.startswith((".", "_")):
                removed_bytes += sum(
                    path.stat().st_size for path in entry.rglob("*") if path.is_file()
                )
                shutil.rmtree(entry)
                removed += 1
        elif entry.name not in PUBLISHED_ICON_FILES:
            removed_bytes += entry.stat().st_size
            entry.unlink()
            removed += 1

    return removed, removed_bytes


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

    removed, removed_bytes = prune_icon_helpers()

    # Remove the now-empty author directories.
    for author_dir in (PUBLIC / "1x1").iterdir():
        if author_dir.is_dir() and not any(author_dir.iterdir()):
            author_dir.rmdir()

    print(
        f"Flattened {len(routes['icons'])} icon pages and "
        f"{len(routes['tags'])} tag pages to .html URLs."
    )
    if removed:
        print(
            f"Removed {removed} build-only icon asset(s) "
            f"({removed_bytes / 1024 / 1024:.1f} MiB) from the output."
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, FileExistsError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
