#!/usr/bin/env python3
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATEGORIES_FILE = REPO_ROOT / "assets" / "icons-metadata" / "list-categories.txt"
OUTPUT_FILE = REPO_ROOT / "_data" / "icons.json"

categories: dict[str, list[dict[str, str]]] = {}

with open(CATEGORIES_FILE, "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            continue
        category, path = line.split(":", 1)
        category = category.strip()
        path = path.strip()
        if "/" not in path:
            continue
        author, icon_name = path.split("/", 1)
        entry = {"author": author, "name": icon_name}
        categories.setdefault(category, []).append(entry)

sorted_categories = sorted(categories.items(), key=lambda x: x[0])

output = []
for cat_name, icons in sorted_categories:
    icons.sort(key=lambda x: x["name"])
    output.append({"name": cat_name, "icons": icons})

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    json.dump({"categories": output}, f)

print(
    f"Generated {OUTPUT_FILE} with {len(output)} categories and {sum(len(c['icons']) for c in output)} icons total"
)
