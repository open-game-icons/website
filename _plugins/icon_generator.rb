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

      # Build indices:
      #   - tag_name -> [{author, name}, ...]
      tag_to_icons = {}
      icon_to_tags = {}

      # Flat search index for client-side filtering on the homepage.
      # Uses short keys to keep the inlined JSON compact.
      search_index = []

      raw_data.each do |author_id, author_data|
        icons = author_data['icons']
        next unless icons

        icons.each do |icon_id, icon_info|
          path = "#{author_id}/#{icon_id}"
          entry = { 'author' => author_id, 'name' => icon_id }

          if icon_info['tags'] && icon_info['tags'].any?
            icon_to_tags[path] = icon_info['tags']
            icon_info['tags'].each do |tag|
              (tag_to_icons[tag] ||= []) << entry
            end
          end

          # Build search index entry: i=id, a=author, k=unique keywords from
          # all fields (icon id, tags) split on hyphens
          words = icon_id.split('-')
          if icon_info['tags']
            icon_info['tags'].each do |tag|
              words.concat(Jekyll::Utils.slugify(tag).split('-'))
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

        icons.each_key do |icon_id|
          dir = File.join('1x1', author_id, icon_id)
          page = Jekyll::PageWithoutAFile.new(site, site.source, dir, 'index.html')
          page.data['layout'] = 'icon'
          page.data['author'] = author_id
          page.data['icon_name'] = icon_id
          site.pages << page
        end
      end

      tag_to_icons.each_value { |icons| icons.sort_by! { |i| i['name'] } }

      # Build slug-keyed version to handle tags that slugify to the same
      # value (e.g. "musical instrument" and "musical-instrument"). Merge
      # their icon lists and use the first-seen variant for display.
      tag_slugs = {}
      tag_to_icons.each do |tag_name, icons|
        slug = Jekyll::Utils.slugify(tag_name)
        if tag_slugs.key?(slug)
          tag_slugs[slug]['icons'].concat(icons)
          tag_slugs[slug]['icons'].uniq! { |i| [i['author'], i['name']] }
        else
          tag_slugs[slug] = { 'name' => tag_name, 'icons' => icons.dup }
        end
      end
      tag_slugs.each_value { |v| v['icons'].sort_by! { |i| i['name'] } }

      # Don't generate pages for tags that only have 1 icon
      tag_slugs.keep_if { |_slug, entry| entry['icons'].length > 1 }

      # Expose data for pages to use (via site.data)
      raw_data['tag_to_icons'] = tag_to_icons
      raw_data['icon_to_tags'] = icon_to_tags
      raw_data['tag_slugs'] = tag_slugs
      raw_data['search_index'] = search_index

      # Generate tag pages
      tag_slugs.each do |_slug, entry|
        slug = Jekyll::Utils.slugify(entry['name'])
        dir = File.join('tags', slug)
        page = Jekyll::PageWithoutAFile.new(site, site.source, dir, 'index.html')
        page.data['layout'] = 'tag_page'
        page.data['list_name'] = entry['name']
        page.data['icons'] = entry['icons']
        site.pages << page
      end
    end
  end
end
