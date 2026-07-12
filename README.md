# Open Game Icons

An open source frontend to browse the [free game icons](https://github.com/game-icons/icons) from [game-icons.net](https://www.game-icons.net).

## Building

1. Generate the icon data file (required before running Jekyll):

   ```bash
   python3 scripts/generate_icon_data.py
   ```

2. Serve with Jekyll:

   ```bash
   bundle exec jekyll serve
   ```

The icon data file is regenerated from `assets/icons-metadata/list-categories.txt` and must be re-run whenever the metadata changes.
