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
# Repository of this website: showcase entries arrive here as pull requests.
SITE_REPO = 'ertugrulkeyvan/pnlcs.com'
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


FLAGS = {'en': 'gb', 'es': 'es', 'de': 'de', 'fr': 'fr', 'pt-br': 'br', 'tr': 'tr', 'ru': 'ru', 'zh': 'cn', 'ja': 'jp'}

# {{logo:slug}} in a page becomes the brand mark. Simple Icons (CC0) where one exists,
# otherwise a monogram in the same box, so every row of logos stays even.
LOGOS = {
    'panelica': 'Panelica', 'cpanel': 'cPanel', 'plesk': 'Plesk', 'directadmin': 'DirectAdmin', 'hestiacp': 'HestiaCP',
    'proxmox': 'Proxmox VE', 'vultr': 'Vultr', 'custom': 'Custom',
    'stripe': 'Stripe', 'paypal': 'PayPal', 'authorizenet': 'Authorize.net', 'mollie': 'Mollie', 'razorpay': 'Razorpay',
    'iyzico': 'iyzico', 'tpay': 'Tpay', 'banktransfer': 'Bank transfer',
    'namecheap': 'Namecheap', 'enom': 'Enom', 'resellerclub': 'ResellerClub', 'openprovider': 'OpenProvider',
    'domainnameapi': 'DomainNameApi', 'hrd': 'HRD', 'manual': 'Manual', 'gogetssl': 'GoGetSSL',
    'docker': 'Docker', 'laravel': 'Laravel', 'php': 'PHP', 'mysql': 'MySQL', 'mariadb': 'MariaDB', 'github': 'GitHub',
    'ubuntu': 'Ubuntu', 'debian': 'Debian', 'almalinux': 'AlmaLinux', 'rockylinux': 'Rocky Linux', 'nginx': 'Nginx',
}


# Brand colours of the Simple Icons marks (from simple-icons 16.33.0 data)
SI_COLORS = {'cpanel': '#FF6C2C', 'plesk': '#52BBE6', 'proxmox': '#E57000', 'vultr': '#007BFC', 'stripe': '#635BFF',
             'paypal': '#002991', 'razorpay': '#0C2451', 'namecheap': '#DE3723', 'docker': '#2496ED', 'laravel': '#FF2D20',
             'php': '#777BB4', 'mysql': '#4479A1', 'mariadb': '#003545', 'github': '#181717',
             'ubuntu': '#E95420', 'debian': '#A81D33', 'almalinux': '#141A31', 'rockylinux': '#10B981', 'nginx': '#009639'}
# Brands whose only official mark is a wordmark: shown instead of the written name
WORDMARKS = set()


def logo_html(slug):
    name = LOGOS.get(slug)
    if name is None:
        sys.exit(f'unknown logo slug: {slug}')
    d = ROOT / 'assets' / 'logos'
    word = ' mark--word' if slug in WORDMARKS else ''
    alt = html.escape(name) if word else ''
    for f in (d / f'{slug}-img.svg', d / f'{slug}.png'):
        if f.exists():
            v = hashlib.sha256(f.read_bytes()).hexdigest()[:8]
            return f'<img class="mark{word}" src="assets/logos/{f.name}?v={v}" alt="{alt}" loading="lazy">'
    svg = d / f'{slug}.svg'
    if svg.exists():
        body = re.sub(r'<title>.*?</title>', '', svg.read_text())
        fill = SI_COLORS.get(slug, 'currentColor')
        return body.replace('<svg ', f'<svg class="mark" aria-hidden="true" focusable="false" fill="{fill}" ', 1)
    letters = name[:3] if name.isupper() else ''.join(w[0] for w in re.findall(r'[A-Z][a-z]*|[a-z]+|\\d', name))[:2].upper()
    return f'<span class="mark mark--mono" aria-hidden="true">{letters}</span>'


def logos_in(text):
    """{{logo:x}}Name -> mark + name; a wordmark replaces the name it stands for."""
    def with_name(m):
        # in lists every mark sits in the same white tile, followed by the plain name
        slug, label = m.group(1), m.group(2)
        if not label.strip():  # a mark on its own (logo clusters) stays large and untiled
            return logo_html(slug) + label
        return f'<span class="lt">{logo_html(slug)}</span>' + label
    text = re.sub(r'\{\{logo:([a-z0-9-]+)\}\}([^<{]*)', with_name, text)
    return re.sub(r'\{\{logo:([a-z0-9-]+)\}\}', lambda m: logo_html(m.group(1)), text)


def icon_html(name):
    """{{icon:name}} -> inline Lucide icon (ISC), stroke follows currentColor."""
    f = ROOT / 'assets' / 'icons' / f'{name}.svg'
    if not f.exists():
        sys.exit(f'unknown icon: {name}')
    svg = re.sub(r'<!--.*?-->', '', f.read_text(), flags=re.S).strip()
    svg = re.sub(r'\s+', ' ', svg).replace('> <', '><')
    svg = re.sub(r'class="[^"]*"', 'class="ico" aria-hidden="true" focusable="false"', svg, count=1)
    return svg.replace('width="24" height="24"', 'width="20" height="20"')


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


# ---------- showcase (data/showcase.json, extended through pull requests) ----------

SHOWCASE_FIELDS = {'name': str, 'url': str, 'description': str, 'sells': list, 'runs_on': list}


def load_showcase():
    entries = json.loads((DATA / 'showcase.json').read_text())
    for i, e in enumerate(entries):
        for key, kind in SHOWCASE_FIELDS.items():
            if not isinstance(e.get(key), kind) or not e.get(key):
                sys.exit(f'data/showcase.json entry {i + 1}: "{key}" is required ({kind.__name__})')
        if not re.match(r'https://', e['url']):
            sys.exit(f'data/showcase.json entry {i + 1}: "url" must start with https://')
        if len(e['description']) > 400:
            sys.exit(f'data/showcase.json entry {i + 1}: "description" is longer than 400 characters')
        shot = e.get('screenshot')
        if shot and not (ROOT / shot).exists():
            sys.exit(f'data/showcase.json entry {i + 1}: screenshot {shot} not found')
    return entries


def showcase_card(e, s, compact=False):
    esc = html.escape
    host = re.sub(r'^https://(www\.)?|/$', '', e['url'])
    shot = ''
    if e.get('screenshot'):
        src = e['screenshot']
        small = src.replace('.webp', '-800.webp')
        srcset = f' srcset="{small} 800w, {src} 1600w"' if (ROOT / small).exists() else ''
        shot = (f'<a class="case-shot" href="{esc(e["url"])}"><img src="{small if srcset else src}"{srcset} '
                f'sizes="(min-width: 900px) 45vw, 100vw" alt="" loading="lazy" width="800" height="500"></a>')
    facts = [(s['showcase_sells'], ', '.join(e['sells'])), (s['showcase_runs_on'], ', '.join(e['runs_on']))]
    if e.get('location'):
        facts.append((s['showcase_location'], e['location']))
    dl = ''.join(f'<dt>{esc(k)}</dt><dd lang="en">{esc(v)}</dd>' for k, v in facts)
    draft = ''  # drafts are listed like any other entry; the flag is for maintainers
    desc = '' if compact else f'<p lang="en">{esc(e["description"])}</p>'
    return (f'<article class="case{" case--compact" if compact else ""}">{shot}<div class="case-body">'
            f'<h3>{esc(e["name"])}</h3><p class="where"><a href="{esc(e["url"])}">{esc(host)}</a></p>{desc}'
            f'<dl>{dl}</dl>{draft}</div></article>')


def showcase_carousel(entries, s):
    """Home page: every showcase entry in a small carousel with story-style progress bars."""
    if not entries:
        return ''
    total = len(entries)
    slides = ''.join(
        f'<div class="sc-slide" role="group" aria-roledescription="slide" '
        f'aria-label="{html.escape(s["carousel_slide"].replace("{n}", str(i + 1)).replace("{total}", str(total)))}"'
        f'{"" if i == 0 else " aria-hidden=\"true\""}>{showcase_card(e, s, compact=True)}</div>'
        for i, e in enumerate(entries))
    if total == 1:
        return f'<div class="sc sc--single">{slides}</div>'
    bars = ''.join(f'<button type="button" class="sc-bar" data-to="{i}" aria-label="{html.escape(s["carousel_slide"].replace("{n}", str(i + 1)).replace("{total}", str(total)))}"><i></i></button>'
                   for i in range(total))
    return (f'<div class="sc" data-carousel data-interval="6500" role="region" aria-roledescription="carousel" '
            f'aria-label="{html.escape(s["carousel_label"])}">'
            f'<div class="sc-viewport"><div class="sc-track" aria-live="off">{slides}</div></div>'
            f'<div class="sc-controls">'
            f'<button type="button" class="sc-btn sc-prev" aria-label="{html.escape(s["carousel_prev"])}">{{{{icon:chevron-left}}}}</button>'
            f'<div class="sc-bars">{bars}</div>'
            f'<button type="button" class="sc-btn sc-toggle" aria-label="{html.escape(s["js_pause"])}">'
            f'<span class="sc-ic-pause">{{{{icon:pause}}}}</span><span class="sc-ic-play">{{{{icon:play}}}}</span></button>'
            f'<button type="button" class="sc-btn sc-next" aria-label="{html.escape(s["carousel_next"])}">{{{{icon:chevron-right}}}}</button>'
            f'</div></div>')


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
        items.append(f'<li><a href="{lang_base(c)}{target}" hreflang="{h}" lang="{h}"{cur}>'
                     f'<img src="/assets/flags/{FLAGS[c]}.svg" alt="" width="20" height="15">{n}</a></li>')
    label = html.escape(f'{s["language"]}: {current}')
    flag = f'<img src="/assets/flags/{FLAGS[code]}.svg" alt="" width="20" height="15">'
    return (f'<details class="lang"><summary aria-label="{label}">{flag}<span>{code.split("-")[0].upper()}</span></summary>'
            f'<ul>{"".join(items)}</ul></details>')


_VERSIONS = {}


def asset_version(path):
    """?v=<content hash> so browsers fetch an image again when it changes."""
    if path not in _VERSIONS:
        f = ROOT / path.lstrip('/')
        _VERSIONS[path] = '?v=' + hashlib.sha256(f.read_bytes()).hexdigest()[:8] if f.exists() else ''
    return _VERSIONS[path]


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
    showcase = load_showcase()
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
            body = body.replace('{{showcase}}', '\n'.join(showcase_card(e, s) for e in showcase))
            body = body.replace('{{showcase_featured}}', showcase_carousel(showcase, s))
            body = body.replace('{{showcase_count}}', str(len(showcase)))
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
                   .replace('{{latest_date}}', html.escape(latest['date']))
                   .replace('{{site_repo}}', SITE_REPO))
            doc = re.sub(r'\{\{icon:([a-z0-9-]+)\}\}', lambda m: icon_html(m.group(1)), doc)
            doc = logos_in(doc)
            # every page links assets from the site root, so /de/… pages find them too
            doc = re.sub(r'(?<=["\s,(])assets/', '/assets/', doc)
            doc = re.sub(r'(/assets/[\w./-]+\.(?:webp|png|jpg|svg))(?![?\w])', lambda m: m.group(1) + asset_version(m.group(1)), doc)
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
