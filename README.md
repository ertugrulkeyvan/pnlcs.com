# pnlcs.com

A proposed redesign of [pnlcs.com](https://pnlcs.com/), the website of [PNLCS](https://github.com/Panelica/pnlcs), the open-source hosting billing platform maintained by the Panelica team.

Static site, no framework. A small Python script (standard library only) assembles the pages, and the output is plain HTML, CSS and JavaScript that any static host can serve.

## Build and preview

```bash
python3 build.py                 # src/ -> site/
python3 -m http.server 8093 --directory site
# open http://127.0.0.1:8093/
```

`python3 build.py --refresh` first copies `CHANGELOG.md` and the theme colours from a PNLCS checkout (set `PNLCS_SRC` to its path).

Deploy the `site/` folder at the domain root. Pages link assets as `/assets/...`.

## Layout

| Path | What it is |
|---|---|
| `src/pages/*.html` | English pages. Each starts with a front-matter comment (`title`, `description`, `section`, optional `heading`, `cta: no`) |
| `src/partials/` | Header, footer and closing call-to-action, shared by every page |
| `src/layout.html` | The document shell: meta tags, JSON-LD, stylesheet and script |
| `src/i18n/<lang>/` | Translations: same file names as `src/pages` and `src/partials`, plus `strings.json` |
| `data/CHANGELOG.md` | Copy of the PNLCS changelog; builds the What's new page and the announcement bar |
| `assets/` | `site.css`, `site.js`, `themes.json` (from `themes/*/theme.json`) and screenshots (from `docs/screenshots`, MIT) |
| `tools/check_i18n.py` | Verifies that translations keep the markup, links, code and placeholders of the English source |
| `PRODUCT.md` | Audience, voice and principles for anyone editing the copy |

## Languages

English is the source, published at the root. Translations are published under `/<lang>/`: es, de, fr, pt-br, tr, ru, zh, ja. A page without a translation falls back to English. Release notes stay in English.

After changing English pages, carry the existing translations over and translate what is new:

```bash
python3 tools/sync_i18n.py                     # reuse translations from the last commit; new strings -> tools/i18n-missing.json
# fill in tools/i18n-missing.json, save a copy as tools/i18n-missing.json.filled, then:
python3 tools/sync_i18n.py --apply tools/i18n-missing.json.filled
python3 tools/check_i18n.py                    # all languages, or e.g. `python3 tools/check_i18n.py de`
```

## Logos

Write `{{logo:stripe}}` in a page and the build puts the brand mark there. Marks come from
[Simple Icons](https://simpleicons.org/) (CC0) in `assets/logos/`; brands without one get a monogram of the same size.
The list of known slugs is `LOGOS` in `build.py`. App and OS logos in `assets/apps/` come from the PNLCS app catalog
(`public/img/apps`). Flags in the language menu come from [flag-icons](https://github.com/lipis/flag-icons) (MIT).

## Add your company to the showcase

If you run PNLCS in production, you can list your company on the [showcase page](https://pnlcs.com/showcase.html) with a pull request.
You can do all of it in the browser.

1. Open [`data/showcase.json`](data/showcase.json) and press the pencil icon. GitHub makes a copy (fork) in your account.
2. Add your entry at the end of the list:

   ```json
   {
     "name": "Your Hosting Co",
     "url": "https://example.com/",
     "location": "Germany",
     "description": "What you sell and how PNLCS is used. English, under 400 characters.",
     "sells": ["Shared hosting", "VPS"],
     "runs_on": ["cPanel", "Stripe"],
     "screenshot": "assets/showcase/your-hosting-co.webp"
   }
   ```

   `name`, `url`, `description`, `sells` and `runs_on` are required. `location` and `screenshot` are optional.
   A screenshot must be a `.webp` of your public website, 1600 px wide, under 300 KB, in `assets/showcase/`.
3. Choose **Propose changes**, then **Create pull request**. Add `?template=showcase.md` to the pull request address to get the checklist.

An automatic check builds the site with your entry. It fails if a required field is missing, the URL is not `https://`, or the screenshot file does not exist.
A maintainer then reviews and merges it. Entries stay in English on every language version of the site.

## List a module or theme

[Modules and themes](https://pnlcs.com/extensions.html) lists modules and themes built for PNLCS by the community.
Free and paid, open and closed source are all welcome. The listing links to your own page; nothing is sold on pnlcs.com.
Every listing is marked as community-built: a maintainer checks that the entry is complete before merging it, but the PNLCS team does not test or support the code.

1. Open [`data/extensions.json`](data/extensions.json), press the pencil icon, and add your entry:

   ```json
   {
     "slug": "your-module",
     "name": "Your Module",
     "type": "module",
     "category": "addon",
     "publisher": "Your Company",
     "publisher_url": "https://example.com/",
     "url": "https://example.com/your-module",
     "summary": "One sentence, under 160 characters.",
     "description": "What it does, how it is installed and how it is supported. Paragraphs are separated by a blank line. Under 1500 characters.",
     "features": ["One line per feature", "At most ten"],
     "tags": ["billing", "sms"],
     "price": "free",
     "license": "MIT",
     "version": "1.2.0",
     "requires": "PNLCS 1.4+",
     "updated": "2026-10-06",
     "source": "https://github.com/you/your-module",
     "demo_url": "https://demo.example.com/",
     "docs_url": "https://example.com/docs/your-module",
     "support_url": "https://example.com/support",
     "changelog_url": "https://example.com/your-module/changes",
     "screenshots": ["assets/extensions/your-module-1.webp"]
   }
   ```

   - Required: `slug`, `name`, `type`, `category`, `publisher`, `publisher_url`, `url`, `summary`, `description`, `price`, `license`, `requires`, `updated`. Everything else is optional.
   - `type` is `module` or `theme`. A module's `category` is `server`, `gateway`, `registrar`, `ssl` or `addon`; a theme's is `theme`.
   - `price` is `free`, `paid` or `freemium` (free and paid). Prices themselves stay on your own page.
   - `url` is where people get it. Every address must start with `https://`.
   - `features`: at most 10 lines, each under 140 characters. `tags`: at most 6 short lowercase words, used by the search.
   - A listing counts as open source when `source` is set and `license` names an open licence (MIT, GPL, Apache, BSD …).
   - Pictures are optional; a listing without them gets a pattern drawn from its slug.
     - Cover: `assets/extensions/<slug>-cover.webp`, 1600 × 800 px, under 300 KB. It tops the card in the directory and
       opens the gallery on the listing page. Without one, the card shows the first screenshot.
     - Screenshots: `.webp`, 1600 × 1000 px, under 300 KB, at most six, listed in `screenshots`.
     - Icon: a square `assets/extensions/<slug>-icon.svg` (or `.png`, `.webp`). Without one, the card shows the initials.
2. Choose **Propose changes**, then **Create pull request**. Add `?template=extension.md` to the pull request address to get the checklist.

The listing gets its own page at `/module-<slug>.html` or `/theme-<slug>.html`, and every publisher gets a page at
`/publisher-<name>.html` with all of their listings. Listings stay in English on every language version of the site.

### Your publisher page

To add a description, a location and a support link to your publisher page, add yourself to [`data/publishers.json`](data/publishers.json).
`name` must be written exactly as `publisher` in your listings:

```json
{
  "name": "Your Company",
  "url": "https://example.com/",
  "location": "Berlin, Germany",
  "description": "Who you are and what you build for PNLCS, under 400 characters.",
  "support_url": "https://example.com/support"
}
```

A square logo can go in `assets/publishers/<name>-logo.svg` (or `.png`, `.webp`), where `<name>` is the publisher in lowercase with dashes.

## Content rules

Every number and feature on the site must be verifiable in the PNLCS repository or its documentation. The site does not publish per-module test status. See `PRODUCT.md`.

Live figures (stars, contributors, latest release, Docker pulls) are fetched in the browser from the GitHub API and shields.io; the HTML carries fallback values.

## License

MIT. Screenshots and theme data come from the PNLCS repository, which is also MIT licensed.
