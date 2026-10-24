_default:
    @just --list

# Rebuild icons.db from icons.sql
db:
    (cd static/assets/icons && ./rebuild_db.sh)

# Generate Zola content, data, and the search index from icons.db
generate:
    python3 scripts/generate.py

# Build the site and restore the legacy .html routes
build: generate
    zola build
    python3 scripts/flatten_urls.py

# Build, flatten, and serve the actual output (no live reload)
serve: build
    python3 -m http.server -d public

# Build and verify the generated page counts and internal links
check: build
    python3 scripts/check_links.py

# Remove generated output and generated source files
clean:
    rm -rf public content/generated data/generated static/search-index.json
