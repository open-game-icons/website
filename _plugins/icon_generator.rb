module IconGenerator
  # Jekyll generator that reads the icon metadata at build time to:
  #   1. Populate site.data.icons for the index page to consume
  #   2. Create a page at /1x1/{author}/{icon_name}/ for every unique icon
  class Generator < Jekyll::Generator
    def generate(site)
      icons_path = File.join(site.source, 'assets', 'icons-metadata', 'list-categories.txt')
      return unless File.exist?(icons_path)

      # Parse every line of the file, which is in the format:
      #   CategoryName: author/icon-name
      categories = {}
      seen = {}

      File.foreach(icons_path) do |line|
        line = line.strip
        next if line.empty?
        next unless line.include?(':')

        category, path = line.split(':', 2)
        category = category.strip
        path = path.strip
        next unless path.include?('/')

        author, icon_name = path.split('/', 2)
        entry = { 'author' => author, 'name' => icon_name }
        (categories[category] ||= []) << entry
        seen[[author, icon_name]] = true
      end

      # Sort categories alphabetically and icons alphabetically within each
      categories = categories.sort_by { |k, _| k }
      categories_data = categories.map do |category_name, icons|
        icons.sort_by! { |i| i['name'] }
        { 'name' => category_name, 'icons' => icons }
      end

      # Expose the data so the index page can use site.data.icons.categories
      site.data['icons'] = { 'categories' => categories_data }

      # Generate a page per unique icon at /1x1/{author}/{icon_name}/
      seen.each_key do |author, icon_name|
        dir = File.join('1x1', author, icon_name)
        page = Jekyll::PageWithoutAFile.new(site, site.source, dir, 'index.html')
        page.data['layout'] = 'icon'
        page.data['author'] = author
        page.data['icon_name'] = icon_name
        site.pages << page
      end
    end
  end
end
