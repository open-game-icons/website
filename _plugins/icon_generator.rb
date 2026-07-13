module IconGenerator
  # Jekyll generator that reads icon metadata at build time to:
  #   1. Populate site.data.icons for the index and category/tag pages
  #   2. Create pages at /categories/<slug>/, /tags/<slug>/, and
  #      /1x1/{author}/{icon_name}/
  class Generator < Jekyll::Generator
    def generate(site)
      categories_path = File.join(site.source, 'assets', 'icons-metadata', 'list-categories.txt')
      tags_path = File.join(site.source, 'assets', 'icons-metadata', 'list-tags.txt')

      category_to_icons = {}
      icon_to_category = {}

      # Parse categories file (format: "CategoryName: author/icon-name")
      # Builds category_to_icons (category name -> array of icon entries)
      # and icon_to_category (reverse lookup)
      if File.exist?(categories_path)
        File.foreach(categories_path) do |line|
          line = line.strip
          next if line.empty?
          next unless line.include?(':')

          category, path = line.split(':', 2)
          category = category.strip
          path = path.strip
          next unless path.include?('/')

          author, icon_name = path.split('/', 2)
          entry = { 'author' => author, 'name' => icon_name }
          (category_to_icons[category] ||= []) << entry
          icon_to_category["#{author}/#{icon_name}"] = category
        end
      end

      # Sort categories alphabetically and icons alphabetically within each
      category_to_icons = category_to_icons.sort_by { |k, _| k }
      categories_data = category_to_icons.map do |category_name, icons|
        icons.sort_by! { |i| i['name'] }
        { 'name' => category_name, 'icons' => icons }
      end

      # Expose so index page can use site.data.icons.categories
      site.data['icons'] = { 'categories' => categories_data }

      tag_to_icons = {}
      icon_to_tags = {}

      # Parse tags file (format: "author/icon-name: tag1, tag2, tag3")
      if File.exist?(tags_path)
        File.foreach(tags_path) do |line|
          line = line.strip
          next if line.empty?
          next unless line.include?(':')

          path, tags_str = line.split(':', 2)
          path = path.strip
          tags_str = tags_str.strip
          next unless path.include?('/')

          author, icon_name = path.split('/', 2)

          tags = tags_str.split(',').map(&:strip).reject(&:empty?)
          tags.each do |tag|
            (tag_to_icons[tag] ||= []) << { 'author' => author, 'name' => icon_name }
          end
          icon_to_tags[path] = tags
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
          tag_slugs[slug] = { 'tag_name' => tag_name, 'icons' => icons.dup }
        end
      end
      tag_slugs.each_value { |v| v['icons'].sort_by! { |i| i['name'] } }

      site.data['icons']['tag_to_icons'] = tag_to_icons
      site.data['icons']['icon_to_tags'] = icon_to_tags
      site.data['icons']['icon_to_category'] = icon_to_category
      site.data['icons']['tag_slugs'] = tag_slugs

      # Generate a page per category at /categories/<slug>/
      categories_data.each do |cat|
        slug = Jekyll::Utils.slugify(cat['name'])
        dir = File.join('categories', slug)
        page = Jekyll::PageWithoutAFile.new(site, site.source, dir, 'index.html')
        page.data['layout'] = 'category_page'
        page.data['category_name'] = cat['name']
        page.data['icons'] = cat['icons']
        site.pages << page
      end

      # Generate a page per tag at /tags/<slug>/
      tag_slugs.each_value do |entry|
        slug = Jekyll::Utils.slugify(entry['tag_name'])
        dir = File.join('tags', slug)
        page = Jekyll::PageWithoutAFile.new(site, site.source, dir, 'index.html')
        page.data['layout'] = 'tag_page'
        page.data['tag_name'] = entry['tag_name']
        page.data['icons'] = entry['icons']
        site.pages << page
      end

      # Generate a page per unique icon at /1x1/{author}/{icon_name}/
      all_icons = categories_data.flat_map { |cat| cat['icons'] }
      all_icons.each do |entry|
        dir = File.join('1x1', entry['author'], entry['name'])
        page = Jekyll::PageWithoutAFile.new(site, site.source, dir, 'index.html')
        page.data['layout'] = 'icon'
        page.data['author'] = entry['author']
        page.data['icon_name'] = entry['name']
        site.pages << page
      end
    end
  end
end
