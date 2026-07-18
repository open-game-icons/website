module IconGenerator
  # Jekyll generator that reads icon metadata from _data/icons.json at build
  # time to:
  #   1. Populate site.data.icons for the index and tag pages
  #   2. Create pages at /tags/<slug>/ and /1x1/{author}/{icon_name}/
  class Generator < Jekyll::Generator
    def generate(site)
      icon_data = site.data['icons']
      tag_data = site.data['tags']
      search_index = []

      icon_data.each do |path, icon_info|
        author_id = icon_info['author']
        icon_id = icon_info['id']

        if icon_info['tags'] && icon_info['tags'].any?
          icon_info['tags'].each do |tag|
            (tag_data[tag]['icons'] ||= []) << path if tag_data[tag]
          end
        end

        # Build search index entry: i=id, a=author, k=unique keywords from
        # all fields (icon id, tags, keywords) split on hyphens and spaces
        icon_name = icon_info['name'] || icon_id
        words = icon_id.split('-')
        words.concat(icon_name.downcase.split)
        if icon_info['tags']
          icon_info['tags'].each do |tag|
            words.concat(Jekyll::Utils.slugify(tag).split('-'))
          end
        end
        if icon_info['keywords']
          icon_info['keywords'].each do |kw|
            words.concat(kw.downcase.split)
          end
        end
        search_index << { 'i' => icon_id, 'a' => author_id, 'k' => words.uniq.sort }

        # Generate a page per unique icon at /1x1/{author}/{icon_name}/
        dir = File.join('1x1', author_id, icon_id)
        page = Jekyll::PageWithoutAFile.new(site, site.source, dir, 'index.html')
        page.data['layout'] = 'icon'
        page.data['author'] = author_id
        page.data['icon_name'] = icon_id
        page.data['display_name'] = icon_info['name'] || icon_id
        site.pages << page
      end

      # Sort tag icon lists by display name.
      tag_data.each_value { |t| t['icons']&.sort_by! { |key| icon_data.dig(key, 'name') || icon_data.dig(key, 'id') || key } }

      # Expose data for pages to use (via site.data)
      site.data['search_index'] = search_index
      site.data['icon_keys'] = icon_data.keys.sort_by { |key| icon_data.dig(key, 'name') || icon_data.dig(key, 'id') || key }

      # Generate tag pages (only for tags with more than 1 icon)
      tag_data.each do |slug, tag_info|
        icons = tag_info['icons']
        next unless icons && icons.length > 1
        dir = File.join('tags', slug)
        page = Jekyll::PageWithoutAFile.new(site, site.source, dir, 'index.html')
        page.data['layout'] = 'tag_page'
        page.data['list_name'] = tag_data.dig(slug, 'name') || slug
        page.data['icons'] = icons
        site.pages << page
      end
    end
  end
end
