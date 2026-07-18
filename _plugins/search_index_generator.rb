require "sqlite3"

module Jekyll
  # Generator that runs after jekyll-sqlite and builds the client-side
  # search index (site.data.search_index) as a lookup table keyed by
  # "icon--{author}--{id}" → array of unique search keywords.
  class SearchIndexGenerator < Jekyll::Generator
    # Lower priority than jekyll-sqlite (which runs at :high)
    priority :low

    def generate(site)
      db_path = File.join(site.source, "_db", "icons.db")
      return unless File.exist?(db_path)

      db = SQLite3::Database.new(db_path, readonly: true)
      db.results_as_hash = true

      lookup = {}

      # Single query: fetch all icons with their tags and keywords joined as CSV
      db.execute(<<~SQL) do |row|
        SELECT i.author, i.id, i.name,
               group_concat(DISTINCT it.tag)     AS tag_list,
               group_concat(DISTINCT ik.keyword) AS keyword_list
        FROM icons i
        LEFT JOIN icon_tags     it ON i.author = it.author AND i.id = it.id
        LEFT JOIN icon_keywords ik ON i.author = ik.author AND i.id = ik.id
        GROUP BY i.author, i.id
      SQL
        # Build search keywords from icon id (split on hyphens), display name
        # (split on spaces), tag slugs, and explicit keywords.
        icon_name = row["name"] || row["id"]
        words = row["id"].split("-")
        words.concat(icon_name.downcase.split)

        if row["tag_list"]
          row["tag_list"].split(",").each do |tag|
            words.concat(Jekyll::Utils.slugify(tag).split("-"))
          end
        end

        if row["keyword_list"]
          row["keyword_list"].split(",").each do |kw|
            words.concat(kw.downcase.split)
          end
        end

        key = "icon--#{row["author"]}--#{row["id"]}"
        lookup[key] = words.uniq.sort
      end

      site.data["search_index"] = lookup
      Jekyll.logger.info "SearchIndexGenerator:", "Built search index (#{lookup.size} entries)"

      db.close
    end
  end
end
