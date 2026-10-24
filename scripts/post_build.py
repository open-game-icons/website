#!/usr/bin/env python3
"""Post-process the Zola build.

Zola copies the entire icon subrepo from static/assets/icons. Only the SVG
directories and licenses belong on the site, so the database, SQL, scripts,
and docs are pruned from the output here.

The legacy .html URLs are produced by Zola aliases declared on each generated
page, so this script does not move or rename any generated pages.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
ICONS = PUBLIC / "assets/icons"
PUBLISHED_ICON_FILES = {"license.txt", "METADATA_LICENSE.txt"}


def prune_icon_helpers() -> tuple[int, int]:
    """Remove build-only files copied from static/assets/icons.

    Keep the author/badge SVG directories and licenses. Everything else at the
    top level is a database, SQL dump, script, or documentation file that does
    not belong on the site.
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
    # Zola emits these by default; the site does not use them.
    (PUBLIC / "robots.txt").unlink(missing_ok=True)
    (PUBLIC / "sitemap.xml").unlink(missing_ok=True)

    removed, removed_bytes = prune_icon_helpers()

    if removed:
        print(
            f"Removed {removed} build-only icon asset(s) "
            f"({removed_bytes / 1024 / 1024:.1f} MiB) from the output."
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
