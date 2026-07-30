---
title: About
layout: page
---

# Frequently Anticipated Questions

## What is this?

**Open Game Icons** is an [open source](https://github.com/open-game-icons/website) continuation of the wonderful [Game-icons.net](https://game-icons.net).
Like its predecessor, Open Game Icons hosts thousands of icons created by several talented artists, all of which are available to use for free under permissive licenses.

## Why make this site? Why use it over Game-icons.net?

Game-icons.net is a fantastic resource, but it has a few issues that inspired me to create Open Game Icons:

1. Although its icons are free and available on [GitHub](https://github.com/game-icons/icons), the Game-icons.net website itself is closed source.
   This means that if the site becomes unmaintained or goes offline (as has briefly happened [many times](https://github.com/game-icons/icons/issues?q=is%3Aissue%20cert)), nobody can easily browse the icons anymore.
2. The metadata (including tags and descriptions) from Game-icons.net is not included in the GitHub repo either, making it difficult to use and impossible to contribute to.
   Furthermore, it's not clear how the metadata is licensed, making certain aspects like the descriptions unsafe to use without permission (see [Is this site legal?](#is-this-site-legal)).
3. As of July 2026, Game-icons.net is not very actively maintained.
   Its repository has hundreds of open issues and dozens of unmerged pull requests.
   To the best of my knowledge, it is maintained solely by [Delapouite](https://github.com/Delapouite) (who also created a huge number of icons on the site!), and I don't blame them for falling behind - that's a lot to keep up with!

With Open Game Icons, I hope to address these shortcomings!

1. As the name implies, the website for Open Game Icons is fully [open source](https://github.com/open-game-icons/website).
   This allows anyone to host their own instance, or even run the site offline, ensuring that the icons will still be accessible even if this particular instance (open-game-icons.net) goes down.
2. The metadata for Open Game Icons is available as a [SQLite database](https://github.com/open-game-icons/icons/blob/master/icons.sql), and it is released into the [public domain](https://creativecommons.org/publicdomain/zero/1.0/) for anyone to use.
3. Open Game Icons uses a [fork](https://github.com/open-game-icons/icons) of the Game-icons.net icon repository.
   This fork includes not only all of the original icons from Game-icons.net, but also the icons from almost every open PR from the original repository!
   I can't promise I'll be a more active maintainer forever, but with the website and metadata fully open-sourced, it'll be much easier for someone else to pick up where I left off!

I'm a big fan of this icon collection, and while I may not necessarily have the artistic skills to contribute to it myself, I wanted to least pay it forward by **giving these free icons the free website they deserve**. :)

## Where's the studio?

Game-icons.net includes a suite of icon editing features known as the "Studio", but I have not gotten around to implementing an equivalent editor for Open Game Icons yet.
Personally, I always just grab the SVGs and edit/export them in [Inkscape](https://inkscape.org/) as needed, so I never really touch the studio myself.
If you normally depend on the studio, I suggest you give the Inkscape workflow a try!

That being said, since this site is [open source](https://github.com/open-game-icons/website), I would welcome contributions from anyone who wants to add icon editing functionality to this site!

## What license does this site use?

- The [code for the website](https://github.com/open-game-icons/website) is licensed under the [GNU Affero General Public License Version 3.0](/LICENSE.txt).
- To the best of my knowledge, the icon metadata used by this site is not copyrightable, but to what extent it is, it is released into the public domain under the terms of the [CC0 1.0 Universal](/METADATA_LICENSE.txt) license.
- Each icon has its own license listed on its respective page.

## How do I contribute an icon?

Check out [CONTRIBUTING.md](https://github.com/open-game-icons/icons/blob/master/CONTRIBUTING.md) over on the [open-game-icons/icons](https://github.com/open-game-icons/icons) repo!

## How do I request an icon?

Open Game Icons is not currently accepting requests for new icons.
If you'd like to see a new icon added to the site, I encourage you to contribute it yourself!

Alternatively, you can submit an icon request upstream to Game-icons.net and hope someone eventually makes it for you.

## I found an issue with the site!

Please open an issue on the [open-game-icons/website](https://github.com/open-game-icons/website) repo.

## Is this site legal?

Yes, or at least I certainly believe so!

- All the icons on this site remain the intellectual property of their creators, and Open Game Icons is redistributing them in compliance with their respective licenses.
  Attribution and licensing information for each icon can be found on that icon's page.
- The tags used on this site are borrowed from Game-icons.net.
  I believe they are considered basic metadata, which is not subject to copyright law, per [copyright.gov](https://www.copyright.gov/what-is-copyright/) and [WIPO](https://www.wipo.int/en/web/copyright/protection).
- Game-icons.net includes descriptions for each icon, but these involve more creativity and their licensing is unclear, so they are not used on this site.
  Instead, the tags and categories from [gameicons-metadata](https://github.com/ArnoldSmith86/gameicons-metadata) (CC0) were used to create a list of keywords for each icon to aid in searchability.

I claim no ownership of nor responsibility for the icons distributed on Open Game Icons.
All intellectual property and trademarks that may be depicted by icons or named in website metadata remain the property of their respective owners.
If you are a copyright holder and you think any content distributed on this site infringes upon your rights, please reach to [legal@open-game-icons.net](legal@open-game-icons.net) and I will take down the infringing content.

## How does the site work?

Open Game Icons is a [static site](https://en.wikipedia.org/wiki/Static_web_page) - there's no custom backend code running on a server somewhere.
It's hosted on [GitHub Pages](https://docs.github.com/pages) and served through [Cloudflare](https://www.cloudflare.com/).

On the frontend, the site uses JavaScript exclusively for the search feature.
In fact, you can use the site with JavaScript disabled entirely, and simply search for icons with your browser's search functionality (Ctrl+F) (although you will miss out on some custom keyword-matching logic).

Open Game Icons doesn't collect any data aside from the anonymous, aggregated analytics that Cloudflare provides.

The site is structured to be highly compatible with Game-icons.net.
You should be able to replace "game-icons.net" with "open-game-icons.net" and get the corresponding icon or tag page.
(If you want to automate this, I recommend checking out the [Redirector](https://einaregilsson.com/redirector/) browser extension.)

## Was this site made with AI?

Yes, but I would not describe it as "vibe coded".
I am an experienced developer; I created my [personal website](https://frie.dev) from scratch years ago, using the same technologies that power this site, so I understand how everything works.
I used OpenCode Go and open-weight models to generate code and assist in debugging, for a total cost of under $3.50.

I understand many people are strongly opposed to AI as a matter of principle, and I respect that viewpoint.
I haven't fully made up my mind on the subject myself, and this isn't the right place to try and unpack my personal opinions.

At the end of the day, regardless of how it was made, the end result is the same.
The site exists now, and it's your choice whether or not you use it.
I hope it was worth it!

I'll also note that, to the best of my knowledge, none of the icons on this site were generated by AI.

## What's the icon used as the site logo?

[Self Love](/1x1/skoll/console-controller.html) by [Lorc](http://lorcblog.blogspot.com/), licensed under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/deed.en). ♥

## Who are you?

Hi!
My name is Aaron.
You can find more about me and my other projects on [my website](https://frie.dev). :)

## More questions?

Maybe the [Game-icons.net FAQ](https://game-icons.net/faq.html) will have the answer?

If not, feel free to reach out to [contact@open-game-icons.net](mailto:contact@open-game-icons.net).
