_default:
    @just --list

# Format code and templates
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

# Build with a local base URL and serve (no live reload)
serve port="8000": generate
    zola build --base-url "http://127.0.0.1:{{ port }}"
    python3 -m http.server {{ port }} -d public

# Build and verify pages, aliases, and internal links
check: build
    python3 scripts/check.py

# Remove generated output and generated source files
clean:
    rm -rf public content/generated data/generated static/search-index.json static/assets/icons
