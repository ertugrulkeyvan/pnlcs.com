#!/usr/bin/env python3
"""Build pnlcs.com into ./site.

    python3 build.py            # build every language from src/ and data/
    python3 build.py --refresh  # first copy CHANGELOG.md + themes from a PNLCS checkout

English pages live in src/pages/*.html and are published at the site root.
Translations live in src/i18n/<code>/ with the same layout (pages/, partials/, strings.json)
and are published under /<code>/. A translated page falls back to English if it is missing.

Each page starts with a front-matter comment:

    <!--
    title: Features
    description: One sentence for search engines.
    section: Product            (breadcrumb parent; omit on the home page)
    heading: Features           (optional breadcrumb label, defaults to title)
    cta: no                     (optional; hides the closing call-to-action band)
    -->

Only the standard library is used.
"""
import hashlib
import html
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
DATA = ROOT / 'data'
OUT = ROOT / 'site'
SITE_URL = 'https://pnlcs.com/'
PNLCS_CHECKOUT = Path(os.environ.get('PNLCS_SRC', Path.home() / 'Desktop/pratix/pnlcs-moduller/kaynak/pnlcs'))

# code (folder), hreflang, native name. English is the source and lives at the root.
LANGS = [
    ('en', 'en', 'English'),
    ('es', 'es', 'Español'),
    ('de', 'de', 'Deutsch'),
    ('fr', 'fr', 'Français'),
    ('pt-br', 'pt-BR', 'Português (Brasil)'),
    ('tr', 'tr', 'Türkçe'),
    ('ru', 'ru', 'Русский'),
    ('zh', 'zh-Hans', '简体中文'),
    ('ja', 'ja', '日本語'),
]


# ---------- data refresh (optional) ----------

def refresh():
    if not PNLCS_CHECKOUT.exists():
        sys.exit(f'PNLCS checkout not found at {PNLCS_CHECKOUT} (set PNLCS_SRC)')
    DATA.mkdir(exist_ok=True)
    shutil.copy(PNLCS_CHECKOUT / 'CHANGELOG.md', DATA / 'CHANGELOG.md')
    themes = []
    for f in sorted((PNLCS_CHECKOUT / 'themes').glob('*/theme.json')):
        d = json.loads(f.read_text())
        themes.append({'slug': f.parent.name, 'name': d['name'],
                       'description': d.get('description', ''), 'colors': d.get('colors', {})})
    (ROOT / 'assets' / 'themes.json').write_text(json.dumps(themes, indent=1))
    print(f'refreshed CHANGELOG.md and {len(themes)} themes from {PNLCS_CHECKOUT}')


# ---------- tiny markdown for the changelog ----------

def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<![\w*])\*([^*\n]+)\*(?!\w)', r'<em>\1</em>', text)

    def link(m):
        label, url = m.group(1), m.group(2)
        if not re.match(r'https?://', url):  # repo-relative links point at GitHub
            url = 'https://github.com/Panelica/pnlcs/blob/main/' + url.lstrip('./')
        return f'<a href="{url}">{label}</a>'
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, text)


def markdown(block):
    """Headings (###), paragraphs and one level of bullet lists — all the changelog uses."""
    out, para, items = [], [], []

    def flush():
        if para:
            out.append('<p>' + inline(' '.join(para)) + '</p>')
            para.clear()
        if items:
            out.append('<ul>' + ''.join('<li>' + inline(' '.join(i)) + '</li>' for i in items) + '</ul>')
            items.clear()

    in_code = False
    for line in block.splitlines():
        if line.startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        s = line.strip()
        if not s:
            flush()
        elif s.startswith('### '):
            flush()
            out.append('<h4>' + inline(s[4:]) + '</h4>')
        elif re.match(r'^[-*] ', s) and not line.startswith('    '):
            if para:
                flush()
            items.append([s[2:]])
        elif items and line.startswith(' '):
            items[-1].append(s)
        elif s.startswith('|'):
            continue  # tables are summarised by the link to the full changelog
        else:
            if items:
                flush()
            para.append(s)
    flush()
    return '\n'.join(out)


def changelog_entries():
    text = (DATA / 'CHANGELOG.md').read_text()
    parts = re.split(r'^## ', text, flags=re.M)[1:]
    entries = []
    for p in parts:
        head, _, body = p.partition('\n')
        date, _, title = head.partition(' — ')
        slug = re.sub(r'[^a-z0-9]+', '-', (date + ' ' + title).lower()).strip('-')
        intro = ''
        m = re.match(r'\s*([^#\-|`\s][^\n]*(?:\n[^\n#\-|`][^\n]*)*)', body)
        if m:
            intro = ' '.join(m.group(1).split())
        counts = {k.lower(): len(re.findall(r'^- ', sec, flags=re.M))
                  for k, sec in re.findall(r'^### (\w+)\n(.*?)(?=^### |\Z)', body, flags=re.M | re.S)}
        entries.append({'date': date.strip(), 'title': title.strip(), 'slug': slug,
                        'intro': intro, 'counts': counts, 'body': markdown(body)})
    return entries


def whats_new_html(entries, s, code):
    rows = []
    if code != 'en':
        rows.append(f'<p class="note" style="margin:0 0 32px">{html.escape(s["release_notes_in_english"])}</p>')
    for e in entries:
        # only categories we can translate get a count badge
        counts = ''.join(f'<li>{n} {html.escape(s["count_" + k])}</li>'
                         for k, n in e['counts'].items() if n and ('count_' + k) in s)
        intro = f'<p class="release-intro">{inline(e["intro"])}</p>' if e['intro'] else ''
        counts_html = f'<ul class="release-counts" lang="{code}">{counts}</ul>' if counts else ''
        rows.append(f'''<article class="release" id="{e['slug']}" lang="en">
  <div class="release-date"><time>{html.escape(e['date'])}</time></div>
  <div class="release-body">
    <h2>{inline(e['title'])}</h2>
    {intro}
    {counts_html}
    <details><summary lang="{code}">{html.escape(s['full_release_notes'])}</summary><div class="prose">{e['body']}</div></details>
  </div>
</article>''')
    return '\n'.join(rows)


# ---------- pages ----------

def parse_page(raw):
    m = re.match(r'<!--\n(.*?)\n-->\n', raw, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(':')
            meta[k.strip()] = v.strip()
        raw = raw[m.end():]
    return meta, raw


def mark_current(fragment, filename):
    return fragment.replace(f'href="{filename}"', f'href="{filename}" aria-current="page"')


def lang_base(code):
    return '/' if code == 'en' else f'/{code}/'


def page_url(code, name):
    return SITE_URL.rstrip('/') + lang_base(code) + ('' if name == 'index.html' else name)


def lang_switcher(code, name, s):
    current = next(n for c, _, n in LANGS if c == code)
    target = '' if name == 'index.html' else name
    items = []
    for c, h, n in LANGS:
        cur = ' aria-current="true"' if c == code else ''
        items.append(f'<li><a href="{lang_base(c)}{target}" hreflang="{h}" lang="{h}"{cur}>{n}</a></li>')
    globe = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">'
             '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z"/></svg>')
    label = html.escape(f'{s["language"]}: {current}')
    return (f'<details class="lang"><summary aria-label="{label}">{globe}<span>{code.split("-")[0].upper()}</span></summary>'
            f'<ul>{"".join(items)}</ul></details>')


def read_localized(code, rel):
    """Translated file if it exists, otherwise the English source."""
    if code != 'en':
        f = SRC / 'i18n' / code / rel
        if f.exists():
            return f.read_text(), True
    return (SRC / rel).read_text(), code == 'en'


def build():
    layout = (SRC / 'layout.html').read_text()
    for asset in ('site.css', 'site.js'):  # cache-busting
        digest = hashlib.sha256((ROOT / 'assets' / asset).read_bytes()).hexdigest()[:10]
        layout = layout.replace(f'assets/{asset}"', f'assets/{asset}?v={digest}"')
    en_strings = json.loads((SRC / 'i18n' / 'strings.en.json').read_text())
    entries = changelog_entries()
    latest = entries[0]
    pages = sorted(p.name for p in (SRC / 'pages').glob('*.html'))

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / 'assets', OUT / 'assets')

    report = []
    for code, hreflang, _ in LANGS:
        s = dict(en_strings)
        sf = SRC / 'i18n' / code / 'strings.json'
        if code != 'en' and sf.exists():
            s.update(json.loads(sf.read_text()))
        header, _ = read_localized(code, 'partials/header.html')
        footer, _ = read_localized(code, 'partials/footer.html')
        cta, _ = read_localized(code, 'partials/cta.html')
        js_strings = {k[3:]: v for k, v in s.items() if k.startswith('js_')}
        outdir = OUT if code == 'en' else OUT / code
        outdir.mkdir(parents=True, exist_ok=True)
        translated = 0

        for name in pages:
            raw, is_translated = read_localized(code, f'pages/{name}')
            translated += is_translated
            meta, body = parse_page(raw)
            body = body.replace('{{whats_new}}', whats_new_html(entries, s, code))
            if meta.get('cta', 'yes') != 'no':
                body += cta
            crumbs = ''
            if meta.get('section'):
                crumbs = (f'<nav class="crumbs" aria-label="{html.escape(s["breadcrumb"])}"><ol>'
                          f'<li><a href="./">{html.escape(s["home"])}</a></li>'
                          f'<li>{html.escape(meta["section"])}</li>'
                          f'<li aria-current="page">{html.escape(meta.get("heading", meta["title"]))}</li></ol></nav>')
            body = body.replace('{{crumbs}}', crumbs)
            title = meta['title'] if name == 'index.html' else f'{meta["title"]} | PNLCS'
            alternates = '\n'.join(f'<link rel="alternate" hreflang="{h}" href="{page_url(c, name)}">' for c, h, _ in LANGS)
            alternates += f'\n<link rel="alternate" hreflang="x-default" href="{page_url("en", name)}">'
            head_extra = alternates + f'\n<script>window.PNLCS_I18N={json.dumps(js_strings, ensure_ascii=False)};</script>'
            hdr = mark_current(header, name).replace('{{lang_switcher}}', lang_switcher(code, name, s))
            doc = (layout
                   .replace('<html lang="en">', f'<html lang="{hreflang}">')
                   .replace('{{title}}', html.escape(title))
                   .replace('{{description}}', html.escape(meta.get('description', '')))
                   .replace('{{url}}', page_url(code, name))
                   .replace('{{head_extra}}', head_extra)
                   .replace('{{header}}', hdr)
                   .replace('{{footer}}', footer)
                   .replace('{{content}}', body)
                   .replace('{{latest_title}}', inline(latest['title']))
                   .replace('{{latest_slug}}', latest['slug'])
                   .replace('{{latest_date}}', html.escape(latest['date'])))
            # every page links assets from the site root, so /de/… pages find them too
            doc = re.sub(r'(?<=["\s,(])assets/', '/assets/', doc)
            leftover = re.findall(r'\{\{\w+\}\}', doc)
            if leftover:
                sys.exit(f'{code}/{name}: unreplaced {leftover}')
            (outdir / name).write_text(doc)
        report.append(f'{code} {translated}/{len(pages)}')

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for name in pages:
        links = ''.join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{page_url(c, name)}"/>' for c, h, _ in LANGS)
        for code, _, _ in LANGS:
            sitemap.append(f'  <url><loc>{page_url(code, name)}</loc>{links}</url>')
    sitemap.append('</urlset>')
    (OUT / 'sitemap.xml').write_text('\n'.join(sitemap) + '\n')
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n')
    print(f'built {len(pages)} pages x {len(LANGS)} languages into {OUT.relative_to(ROOT)}/  (translated: {", ".join(report)})')


if __name__ == '__main__':
    if '--refresh' in sys.argv:
        refresh()
    build()
