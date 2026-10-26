_default:
    @just --list

# Format everything (code, templates, docs, etc.)
fmt:
    dprint fmt

# Stop any running `zola serve` processes
kill-serve:
    -pkill -f '[z]ola serve'

# Rebuild icons.db from icons.sql
db:
    (cd icons && ./rebuild_db.sh)

# Generate Zola content, data, search index, and static icon staging from icons.db
generate: kill-serve db
    python3 scripts/generate.py

# Compile the TypeScript sources into static/js
js:
    bun run build:js

# Type-check the TypeScript sources
js-check:
    bun run check:js

# Build the site
build: generate js
    zola build

# Serve with Zola's live reload
# NOTE: does NOT rebuild TypeScript on change; `bun build --watch` doesn't
# gracefully handle editors deleting and rewriting files on save
serve port="8000": generate js
    zola serve --port {{ port }} --open

# Build and verify pages, aliases, and internal links
check: build
    bun run check:js
    dprint check
    ty check
    tombi check
    (cd icons && ./check-svgs.sh)
    zola check --skip-external-links
    python3 scripts/check.py

# Remove generated output and generated source files
clean: kill-serve
    rm -rf public content/generated data/generated static/search-index.json static/icons static/js
