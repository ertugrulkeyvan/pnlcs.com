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

## Content rules

Every number and feature on the site must be verifiable in the PNLCS repository or its documentation. The site does not publish per-module test status. See `PRODUCT.md`.

Live figures (stars, contributors, latest release, Docker pulls) are fetched in the browser from the GitHub API and shields.io; the HTML carries fallback values.

## License

MIT. Screenshots and theme data come from the PNLCS repository, which is also MIT licensed.
