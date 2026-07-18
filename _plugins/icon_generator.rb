module IconGenerator
  # Jekyll generator that reads icon metadata from _data/icons.json at build
  # time to:
  #   1. Populate site.data.icons for the index and tag pages
  #   2. Create pages at /tags/<slug>/ and /1x1/{author}/{icon_name}/
  class Generator < Jekyll::Generator
    def generate(site)
      raw_data = site.data['icons']
      if raw_data.nil? || raw_data.empty?
        Jekyll.logger.warn 'IconGenerator:', 'No icon data found in _data/icons.json'
        return
      end

      # Build tag_key -> whole-object lookup from _data/tags.json for
      # future use by templates and the generator.
      tag_data = site.data['tags'] || {}

      # Build indices:
      #   - tag_name -> [{author, name}, ...]
      tag_to_icons = {}
      icon_to_tags = {}

      # Flat search index for client-side filtering on the homepage.
      # Uses short keys to keep the inlined JSON compact.
      search_index = []

      # Flat list of all icons for the homepage grid.
      all_icons = []

      raw_data.each do |author_id, author_data|
        icons = author_data['icons']
        next unless icons

        icons.each do |icon_id, icon_info|
          path = "#{author_id}/#{icon_id}"
          entry = { 'author' => author_id, 'name' => icon_id, 'display_name' => icon_info['name'] || icon_id }

          all_icons << entry

          if icon_info['tags'] && icon_info['tags'].any?
            icon_to_tags[path] = icon_info['tags']
            icon_info['tags'].each do |tag|
              (tag_to_icons[tag] ||= []) << entry
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
          search_entry = { 'i' => icon_id, 'a' => author_id, 'k' => words.uniq.sort }
          search_index << search_entry
        end
      end

      # Generate a page per unique icon at /1x1/{author}/{icon_name}/
      raw_data.each do |author_id, author_data|
        next unless author_data.is_a?(Hash)
        icons = author_data['icons']
        next unless icons

        icons.each do |icon_id, icon_info|
          dir = File.join('1x1', author_id, icon_id)
          page = Jekyll::PageWithoutAFile.new(site, site.source, dir, 'index.html')
          page.data['layout'] = 'icon'
          page.data['author'] = author_id
          page.data['icon_name'] = icon_id
          page.data['display_name'] = icon_info['name'] || icon_id
          site.pages << page
        end
      end

      tag_to_icons.each_value { |icons| icons.sort_by! { |i| i['display_name'] } }

      # Sort all icons by display name for the homepage grid
      all_icons.sort_by! { |i| i['display_name'] }

      # Expose data for pages to use (via site.data)
      raw_data['all_icons'] = all_icons
      raw_data['tag_to_icons'] = tag_to_icons
      raw_data['icon_to_tags'] = icon_to_tags
      raw_data['tag_data'] = tag_data
      raw_data['search_index'] = search_index

      # Generate tag pages (only for tags with more than 1 icon)
      tag_to_icons.each do |slug, icons|
        next unless icons.length > 1
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
