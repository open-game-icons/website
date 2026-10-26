_default:
    @just --list

# Format everything (code, templates, docs, etc.)
fmt:
    dprint fmt

# Rebuild icons.db from icons.sql
db:
    (cd icons && ./rebuild_db.sh)

# Generate Zola content, data, search index, and static icon staging from icons.db
generate: db
    python3 scripts/generate.py

# Build the site
build: generate
    zola build

# Serve with Zola's live reload
serve port="8000": generate
    zola serve --port {{ port }} --open

# Build and verify pages, aliases, and internal links
check: build
    dprint check
    ty check
    tombi check
    (cd icons && ./check-svgs.sh)
    zola check --skip-external-links
    python3 scripts/check.py

# Remove generated output and generated source files
clean:
    rm -rf public content/generated data/generated static/search-index.json static/assets/icons
