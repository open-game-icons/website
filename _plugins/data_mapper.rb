module Jekyll
  # Generator that converts jekyll-sqlite data arrays into hash lookups
  # so that Liquid templates can avoid expensive `where` filter scans.
  # Runs at :low priority, after jekyll-sqlite (which runs at :high).
  class DataMapper < Jekyll::Generator
    priority :low

    def generate(site)
      map_tag_info(site)
      map_tag_icons(site)
      map_search_index(site)
    end

    private

    # tag_info_array => tag_info
    # Hash: tag_id => { "name" => …, "count" => …, "parent" => … }
    # Used by: _includes/tag_links.html
    def map_tag_info(site)
      data = site.data["tag_info_array"]
      return unless data

      hash = {}
      data.each { |t| hash[t["id"]] = { "name" => t["name"], "count" => t["count"], "parent" => t["parent"] } }
      site.data["tag_info"] = hash
    end

    # tag_icons_array => tag_icons
    # Hash: tag_id => [icon, …]
    # Used by: _layouts/tag_page.html
    def map_tag_icons(site)
      data = site.data["tag_icons_array"]
      return unless data

      hash = {}
      data.each do |icon|
        tag = icon["tag"]
        hash[tag] ||= []
        hash[tag] << icon
      end
      site.data["tag_icons"] = hash
    end

    # search_index_array => search_index
    # Hash: "icon--{author}--{id}" => [unique search keywords]
    # Used by: search-index.json
    def map_search_index(site)
      data = site.data["search_index_array"]
      return unless data

      lookup = {}

      data.each do |row|
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
      Jekyll.logger.info "DataMapper:", "Built search index (#{lookup.size} entries)"
    end
  end
end
