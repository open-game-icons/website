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

# Build with a local base URL, post-process, and serve (no live reload)
serve port="8000": generate
    zola build --base-url "http://127.0.0.1:{{ port }}"
    python3 scripts/post_build.py
    python3 -m http.server {{ port }} -d public

# Build and verify the generated page counts and internal links
check: build
    python3 scripts/check.py

# Remove generated output and generated source files
clean:
    rm -rf public content/generated data/generated static/search-index.json
