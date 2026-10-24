_default:
    @just --list

# Format code and templates
fmt:
    dprint fmt

# Rebuild icons.db from icons.sql
db:
    (cd static/assets/icons && ./rebuild_db.sh)

# Generate Zola content, data, and the search index from icons.db
generate: db
    python3 scripts/generate.py

# Build the site and post-process the output
build: generate
    zola build
    python3 scripts/post_build.py

# Build, post-process, and serve the actual output (no live reload)
serve: build
    python3 -m http.server -d public

# Build and verify the generated page counts and internal links
check: build
    python3 scripts/check.py

# Remove generated output and generated source files
clean:
    rm -rf public content/generated data/generated static/search-index.json
