module IconGenerator
  # Jekyll generator that reads icon metadata from _data/icons.json at build
  # time to:
  #   1. Populate site.data.icons for the index and category/tag pages
  #   2. Create pages at /categories/<slug>/, /tags/<slug>/, and
  #      /1x1/{author}/{icon_name}/
  class Generator < Jekyll::Generator
    def generate(site)
      raw_data = site.data['icons']
      if raw_data.nil? || raw_data.empty?
        Jekyll.logger.warn 'IconGenerator:', 'No icon data found in _data/icons.json'
        return
      end

      # Build indices (and their inverses):
      #   - category_name -> [{author, name}, ...]
      #   - tag_name -> [{author, name}, ...]
      category_to_icons = {}
      icon_to_category = {}
      tag_to_icons = {}
      icon_to_tags = {}

      raw_data.each do |author_id, author_data|
        icons = author_data['icons']
        next unless icons

        icons.each do |icon_id, icon_info|
          path = "#{author_id}/#{icon_id}"
          entry = { 'author' => author_id, 'name' => icon_id }

          if icon_info['category']
            category = icon_info['category']
            (category_to_icons[category] ||= []) << entry
            icon_to_category[path] = category
          end

          if icon_info['tags'] && icon_info['tags'].any?
            icon_to_tags[path] = icon_info['tags']
            icon_info['tags'].each do |tag|
              (tag_to_icons[tag] ||= []) << entry
            end
          end
        end
      end

      # Sort categories alphabetically and icons alphabetically within each
      category_to_icons = category_to_icons.sort_by { |k, _| k }
      categories_data = category_to_icons.map do |category_name, icons|
        icons.sort_by! { |i| i['name'] }
        { 'name' => category_name, 'icons' => icons }
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
      raw_data['categories'] = categories_data
      raw_data['tag_to_icons'] = tag_to_icons
      raw_data['icon_to_tags'] = icon_to_tags
      raw_data['icon_to_category'] = icon_to_category
      raw_data['tag_slugs'] = tag_slugs

      # Generate category and tag pages
      add_list_pages(site, 'categories', 'category_page', categories_data)
      add_list_pages(site, 'tags', 'tag_page', tag_slugs.values)
    end

    private

    # Create listing pages at /<dir_prefix>/<slug>/ for each entry.
    # Each entry must have 'name' and 'icons' keys.
    def add_list_pages(site, dir_prefix, layout, entries)
      entries.each do |entry|
        slug = Jekyll::Utils.slugify(entry['name'])
        dir = File.join(dir_prefix, slug)
        page = Jekyll::PageWithoutAFile.new(site, site.source, dir, 'index.html')
        page.data['layout'] = layout
        page.data['list_name'] = entry['name']
        page.data['icons'] = entry['icons']
        site.pages << page
      end
    end
  end
end
