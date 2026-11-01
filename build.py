#!/usr/bin/env python3
"""Build pnlcs.com into ./site.

    python3 build.py            # build every language from src/ and data/
    python3 build.py --refresh  # first copy CHANGELOG.md + themes from a PNLCS checkout
    python3 build.py --offline  # do not ask shields.io for the project numbers; use data/stats.json

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

Write {{offer}} in a page for the "start a hosting company" band (src/partials/offer.html).
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
# Web3Forms access key for the discovery call form (public by design; set it here or in WEB3FORMS_KEY).
WEB3FORMS_KEY = os.environ.get('WEB3FORMS_KEY', '6592ffbb-2b49-497c-b0f5-a1201b785cbb')
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
        version = ''
        if re.fullmatch(r'\d+\.\d+\.\d+(?:-[\w.]+)?', date.strip()):
            # numbered releases (1.3.0 on) head with "<version> — <date>" and have no title of their own
            version, date, title = date.strip(), title, f'PNLCS {date.strip()}'
        slug = re.sub(r'[^a-z0-9]+', '-', (date + ' ' + title).lower()).strip('-')
        intro = ''
        m = re.match(r'\s*([^#\-|`\s][^\n]*(?:\n[^\n#\-|`][^\n]*)*)', body)
        if m:
            intro = ' '.join(m.group(1).split())
        counts = {k.lower(): len(re.findall(r'^- ', sec, flags=re.M))
                  for k, sec in re.findall(r'^### (\w+)\n(.*?)(?=^### |\Z)', body, flags=re.M | re.S)}
        entries.append({'date': date.strip(), 'title': title.strip(), 'slug': slug, 'version': version,
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
    # "sells" and "runs_on" stay in the data but are not shown: the card reads as a list of tags otherwise
    # a location with a showcase_location_<name> string ("Europe") is shown in the page language
    loc = e.get('location', '')
    key = 'showcase_location_' + re.sub(r'[^a-z0-9]+', '_', loc.lower()).strip('_')
    facts = [(s['showcase_location'], s[key] if key in s else loc, '' if key in s else ' lang="en"')] if loc else []
    dl = ''.join(f'<dt>{esc(k)}</dt><dd{lang}>{esc(v)}</dd>' for k, v, lang in facts)
    dl = f'<dl>{dl}</dl>' if dl else ''
    draft = ''  # drafts are listed like any other entry; the flag is for maintainers
    desc = '' if compact else f'<p lang="en">{esc(e["description"])}</p>'
    return (f'<article class="case{" case--compact" if compact else ""}">{shot}<div class="case-body">'
            f'<h3>{esc(e["name"])}</h3><p class="where"><a href="{esc(e["url"])}">{esc(host)}</a></p>{desc}'
            f'{dl}{draft}</div></article>')


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


# ---------- modules & themes (data/extensions.json, extended through pull requests) ----------
#
# A directory that looks and works like a marketplace, but sells nothing: every listing is
# written by its publisher, and every "get it" button leaves pnlcs.com for the publisher's page.
# Generated pages: extensions.html (browse), <type>-<slug>.html (listing), publisher-<slug>.html.

EXT_TYPES = {'module': ('server', 'gateway', 'registrar', 'ssl', 'addon'), 'theme': ('theme',)}
EXT_CATS = EXT_TYPES['module'] + EXT_TYPES['theme']
EXT_PRICES = ('free', 'freemium', 'paid')
EXT_REQUIRED = {'slug': str, 'name': str, 'type': str, 'category': str, 'publisher': str, 'publisher_url': str,
                'url': str, 'summary': str, 'description': str, 'price': str, 'license': str, 'requires': str,
                'updated': str}
EXT_LINKS = ('source', 'docs_url', 'support_url', 'demo_url', 'changelog_url')
EXT_OPEN_LICENSES = re.compile(r'\b(MIT|BSD|Apache|GPL|LGPL|AGPL|MPL|ISC|Unlicense|CC0)\b', re.I)
EXT_HUES = 6  # monogram colours, picked from the slug so a listing keeps its colour


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def load_publishers():
    """data/publishers.json is optional: a publisher's own description, location and support page."""
    f = DATA / 'publishers.json'
    if not f.exists():
        return {}
    out = {}
    for i, p in enumerate(json.loads(f.read_text())):
        where = f'data/publishers.json entry {i + 1}'
        for key in ('name', 'url'):
            if not isinstance(p.get(key), str) or not p[key].strip():
                sys.exit(f'{where}: "{key}" is required')
        for key in ('url', 'support_url'):
            if p.get(key) and not p[key].startswith('https://'):
                sys.exit(f'{where}: "{key}" must start with https://')
        if len(p.get('description', '')) > 400:
            sys.exit(f'{where}: "description" is longer than 400 characters')
        out[slugify(p['name'])] = p
    return out


def load_extensions():
    entries = json.loads((DATA / 'extensions.json').read_text())
    seen = set()
    for i, e in enumerate(entries):
        where = f'data/extensions.json entry {i + 1}'
        for key, kind in EXT_REQUIRED.items():
            if not isinstance(e.get(key), kind) or not e.get(key).strip():
                sys.exit(f'{where}: "{key}" is required ({kind.__name__})')
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', e['slug']) or len(e['slug']) > 40:
            sys.exit(f'{where}: "slug" must be lowercase letters, digits and dashes, at most 40 characters')
        if e['slug'] in seen:
            sys.exit(f'{where}: slug "{e["slug"]}" is used twice')
        seen.add(e['slug'])
        if e['type'] not in EXT_TYPES:
            sys.exit(f'{where}: "type" must be one of {", ".join(EXT_TYPES)}')
        if e['category'] not in EXT_TYPES[e['type']]:
            sys.exit(f'{where}: "category" for a {e["type"]} must be one of {", ".join(EXT_TYPES[e["type"]])}')
        if e['price'] not in EXT_PRICES:
            sys.exit(f'{where}: "price" must be one of {", ".join(EXT_PRICES)}')
        for key in ('url', 'publisher_url') + EXT_LINKS:
            if e.get(key) and not re.match(r'https://', e[key]):
                sys.exit(f'{where}: "{key}" must start with https://')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', e['updated']):
            sys.exit(f'{where}: "updated" must be a date like 2026-10-06')
        if len(e['summary']) > 160:
            sys.exit(f'{where}: "summary" is longer than 160 characters')
        if len(e['description']) > 1500:
            sys.exit(f'{where}: "description" is longer than 1500 characters')
        if len(e['requires']) > 40 or len(e['license']) > 40 or len(e.get('version', '')) > 20:
            sys.exit(f'{where}: "requires", "license" and "version" must be short (40, 40 and 20 characters)')
        features, tags = e.get('features', []), e.get('tags', [])
        if not isinstance(features, list) or len(features) > 10 or any(len(f) > 140 for f in features):
            sys.exit(f'{where}: "features" is a list of at most 10 lines, each under 140 characters')
        if not isinstance(tags, list) or len(tags) > 6 or any(not re.fullmatch(r'[a-z0-9][a-z0-9 .+-]{0,23}', t) for t in tags):
            sys.exit(f'{where}: "tags" is a list of at most 6 short lowercase words')
        for shot in e.get('screenshots', []):
            if not re.fullmatch(r'assets/extensions/[\w.-]+\.webp', shot) or not (ROOT / shot).exists():
                sys.exit(f'{where}: screenshot {shot} must be an existing .webp in assets/extensions/')
        if len(e.get('screenshots', [])) > 6:
            sys.exit(f'{where}: at most 6 screenshots')
        e['_pub'] = slugify(e['publisher'])
        e['_open'] = bool(e.get('source')) and bool(EXT_OPEN_LICENSES.search(e['license']))
    return sorted(entries, key=lambda e: e['name'].lower())


def publisher_index(entries, publishers):
    """Every publisher that has a listing, merged with data/publishers.json when it has an entry."""
    out = {}
    for e in entries:
        p = out.setdefault(e['_pub'], dict(publishers.get(e['_pub'], {})))
        p.setdefault('name', e['publisher'])
        p.setdefault('url', e['publisher_url'])
        p['slug'] = e['_pub']
        p.setdefault('items', []).append(e)
    return dict(sorted(out.items(), key=lambda kv: kv[1]['name'].lower()))


def pub_count(s, n):
    return s['ext_pub_count_one' if n == 1 else 'ext_pub_count'].replace('{n}', str(n))


def ext_page_name(e):
    return f'{e["type"]}-{e["slug"]}.html'


def pub_page_name(slug):
    return f'publisher-{slug}.html'


def _hue(text):
    return int(hashlib.sha256(text.encode()).hexdigest(), 16) % EXT_HUES


def _monogram(name):
    return ''.join(w[0] for w in re.findall(r'[A-Za-z0-9]+', name))[:2].upper() or '?'


def ext_mark(e, size=''):
    cls = f'ext-mark{" ext-mark--" + size if size else ""}'
    for ext in ('svg', 'png', 'webp'):
        f = ROOT / 'assets' / 'extensions' / f'{e["slug"]}-icon.{ext}'
        if f.exists():
            return f'<img class="{cls}" src="assets/extensions/{f.name}" alt="" width="56" height="56" loading="lazy">'
    return f'<span class="{cls} ext-mark--mono ext-hue-{_hue(e["slug"])}" aria-hidden="true">{html.escape(_monogram(e["name"]))}</span>'


def ext_cover_file(e):
    """The publisher's own cover, assets/extensions/<slug>-cover.webp (2:1), if there is one."""
    for ext in ('webp', 'png', 'jpg'):
        f = ROOT / 'assets' / 'extensions' / f'{e["slug"]}-cover.{ext}'
        if f.exists():
            return f'assets/extensions/{f.name}'
    return None


def ext_pattern(slug, cols=12, rows=6):
    """A cover for a listing without pictures: a grid of soft shapes drawn from the slug, so every listing has its own and
    it never changes between builds (the idea of WordPress.org's generated plugin banners)."""
    step = 50
    h = hashlib.shake_256(slug.encode()).digest(cols * rows * 2)
    shapes = []
    for i in range(cols * rows):
        v, w = h[i], h[cols * rows + i]
        if v % 5 < 3:  # most cells stay empty, so the pattern reads as calm texture
            continue
        x, y, o, r = (i % cols) * step + 25, (i // cols) * step + 25, .06 + (w % 5) * .04, 9 + w % 4 * 3
        if w % 3 == 0:
            shapes.append(f'<circle cx="{x}" cy="{y}" r="{r}" opacity="{o:.2f}"/>')
        elif w % 3 == 1:
            shapes.append(f'<rect x="{x - r}" y="{y - r}" width="{2 * r}" height="{2 * r}" rx="{r // 2}" opacity="{o:.2f}"/>')
        else:
            shapes.append(f'<path d="M{x} {y - r - 3}L{x + r + 3} {y}L{x} {y + r + 3}L{x - r - 3} {y}Z" opacity="{o:.2f}"/>')
    return (f'<svg class="ext-pattern" viewBox="0 0 {cols * step} {rows * step}" preserveAspectRatio="xMidYMid slice" '
            f'aria-hidden="true" fill="currentColor">{"".join(shapes)}</svg>')


def ext_cover_inner(e, card=True):
    """Cover picture: the publisher's cover, then (on a card) the first screenshot, then a placeholder."""
    src = ext_cover_file(e) or (card and (e.get('screenshots') or [None])[0])
    if src:
        return f'<img src="{html.escape(src)}" alt="" loading="lazy" width="1600" height="800">'
    if e['type'] == 'theme' and card:  # a theme placeholder looks like a page
        return f'<span class="xc-ph ext-hue-{_hue(e["slug"])}" aria-hidden="true"><i></i><i></i><i></i></span>'
    return f'<span class="ext-ph ext-hue-{_hue(e["slug"])}" aria-hidden="true">{ext_pattern(e["slug"])}</span>'


def pub_mark(p, size=''):
    cls = f'ext-mark ext-mark--pub{" ext-mark--" + size if size else ""}'
    for ext in ('svg', 'png', 'webp'):
        f = ROOT / 'assets' / 'publishers' / f'{p["slug"]}-logo.{ext}'
        if f.exists():
            return f'<img class="{cls}" src="assets/publishers/{f.name}" alt="" width="56" height="56" loading="lazy">'
    return f'<span class="{cls} ext-mark--mono ext-hue-{_hue(p["slug"])}" aria-hidden="true">{html.escape(_monogram(p["name"]))}</span>'


def ext_price_badge(e, s, big=False):
    return (f'<span class="price price--{e["price"]}{" price--big" if big else ""}">'
            f'{html.escape(s["ext_price_" + e["price"]])}</span>')


def _date(iso):
    # shown as written; site.js turns it into the visitor's own date format
    return f'<time datetime="{iso}" data-date>{iso}</time>'


def _host(url):
    return re.sub(r'^https://(www\.)?', '', url).rstrip('/')


def ext_card(e, s, filters=True):
    esc = html.escape
    by = esc(s['ext_by']).replace('{publisher}', f'<span lang="en">{esc(e["publisher"])}</span>')
    cover = f'<span class="xc-cover">{ext_cover_inner(e)}</span>'
    open_src = f'<span class="xc-open" title="{esc(s["ext_open_source"])}">{{{{icon:code}}}}<span class="visually-hidden">{esc(s["ext_open_source"])}</span></span>' if e['_open'] else ''
    data = ''
    if filters:
        words = ' '.join([e['name'], e['summary'], e['publisher'], s['ext_cat_' + e['category']], ' '.join(e.get('tags', []))])
        data = (f' data-type="{e["type"]}" data-cat="{e["category"]}" data-price="{e["price"]}" data-pub="{e["_pub"]}"'
                f' data-open="{int(e["_open"])}" data-updated="{e["updated"]}" data-name="{esc(e["name"].lower())}"'
                f' data-q="{esc(words.lower())}"')
    return (f'<li class="xc xc--{e["type"]}"{data}><a class="xc-link" href="{ext_page_name(e)}">{cover}'
            f'<span class="xc-top">{ext_mark(e)}<span class="xc-id"><strong lang="en">{esc(e["name"])}</strong>'
            f'<span class="xc-pub">{by}</span></span></span>'
            f'<span class="xc-sum" lang="en">{esc(e["summary"])}</span>'
            f'<span class="xc-foot"><span class="xc-cat">{esc(s["ext_cat_" + e["category"]])}</span>{open_src}'
            f'{ext_price_badge(e, s)}</span></a></li>')


def ext_grid(items, s, filters=False):
    return f'<ul class="xm-grid">{"".join(ext_card(e, s, filters) for e in items)}</ul>'


def ext_notice(s, cls=''):
    return (f'<div class="notice{cls}" role="note"><h2>{html.escape(s["ext_notice_title"])}</h2>'
            f'<p>{html.escape(s["ext_notice_body"])}</p><p>{html.escape(s["ext_notice_check"])}</p></div>')


def ext_add_section(s):
    esc = html.escape
    steps = ''.join(f'<li><span><strong>{esc(s[f"ext_add_step{i}"])}</strong><span>{esc(s[f"ext_add_step{i}_d"])}</span></span></li>'
                    for i in (1, 2, 3))
    return f'''<section class="band" id="add">
  <div class="wrap split split--top">
    <div class="split-copy">
      <h2>{esc(s["ext_add_title"])}</h2>
      <p class="lede">{esc(s["ext_add_lede"])}</p>
      <div class="btn-row" style="margin-top:28px">
        <a class="btn btn--navy" href="https://github.com/{{{{site_repo}}}}/edit/main/data/extensions.json" data-cta="extension-add">{esc(s["ext_add_edit"])}</a>
        <a class="btn btn--ghost" href="https://github.com/{{{{site_repo}}}}#list-a-module-or-theme">{esc(s["ext_add_guide"])}</a>
      </div>
    </div>
    <ol class="steps">{steps}</ol>
  </div>
</section>'''


def ext_browser(entries, pubs, s):
    """The whole of extensions.html below the front matter: search, filters, results, notice, how to list."""
    esc = html.escape
    count = lambda key, value: sum(1 for e in entries if e[key] == value)
    stats = [(len(entries), s['ext_stat_listings']), (count('type', 'module'), s['ext_stat_modules']),
             (count('type', 'theme'), s['ext_stat_themes']), (len(pubs), s['ext_stat_publishers'])]
    stats_html = ''.join(f'<li><b>{n}</b><span>{esc(label)}</span></li>' for n, label in stats if n)
    chips = [f'<button type="button" class="xm-chip" data-chip="" aria-pressed="true">{esc(s["ext_all"])}</button>']
    chips += [f'<button type="button" class="xm-chip" data-chip="{c}" aria-pressed="false">{esc(s["ext_cat_" + c])}'
              f'<span>{count("category", c)}</span></button>' for c in EXT_CATS if count('category', c)]

    def option(kind, name, value, label, n, checked=False, keep=False):
        # an option with nothing behind it is left out, except in the short fixed groups (type, price, source),
        # which stay complete and greyed so a visitor sees what kinds of listing can exist
        if not n and not keep:
            return ''
        return (f'<li><label class="xm-opt{"" if n else " is-empty"}"><input type="{kind}" name="{name}" value="{value}"'
                f'{" checked" if checked else ""}{"" if n else " disabled"}><span>{label}</span><small>{n}</small></label></li>')

    types = option('radio', 'type', '', esc(s['ext_all']), len(entries), True) + ''.join(
        option('radio', 'type', t, esc(s['ext_type_' + t + 's']), count('type', t), keep=True) for t in EXT_TYPES)
    cats = ''.join(option('checkbox', 'cat', c, esc(s['ext_cat_' + c]), count('category', c)) for c in EXT_CATS)
    prices = ''.join(option('checkbox', 'price', p, esc(s['ext_price_' + p]), count('price', p), keep=True) for p in EXT_PRICES)
    opened = option('checkbox', 'open', '1', esc(s['ext_filter_open']), sum(e['_open'] for e in entries), keep=True)
    fieldset = lambda legend, opts, cls='': (f'<fieldset{cls}><legend>{esc(legend)}</legend><ul>{opts}</ul></fieldset>' if opts else '')
    pub_opts = ''.join(option('checkbox', 'pub', slug, f'<span lang="en">{esc(p["name"])}</span>', len(p['items']))
                       for slug, p in pubs.items())
    groups = ''.join(
        f'<section class="xm-group" data-group="{t}" aria-labelledby="xm-h-{t}"><div class="xm-group-head">'
        f'<h2 id="xm-h-{t}">{esc(s["ext_type_" + t + "s"])}</h2><span class="xm-group-n"></span>'
        + (f'<p class="xm-group-link">{esc(s["ext_builtin_ask"])} <a href="themes.html">{esc(s["ext_official_themes"])}</a></p>' if t == 'theme' else '')
        + '</div>'
        f'{ext_grid([e for e in entries if e["type"] == t], s, filters=True)}'
        f'<button type="button" class="btn btn--ghost xm-group-more" data-more-type="{t}" hidden>{esc(s["ext_view_all"])} '
        f'<span>({count("type", t)})</span></button></section>'
        for t in EXT_TYPES if count('type', t))
    sorts = ''.join(f'<option value="{k}">{esc(s["ext_sort_" + k])}</option>' for k in ('updated', 'name'))
    empty = (f'<div class="ext-empty"><p>{esc(s["ext_empty"])}</p>'
             f'<a class="btn btn--ghost" href="#add">{esc(s["ext_list_yours"])}</a></div>') if not entries else ''
    pub_cards = ''.join(
        f'<li><a href="{pub_page_name(slug)}">{pub_mark(p)}<span><strong lang="en">{esc(p["name"])}</strong>'
        f'<small>{esc(pub_count(s, len(p["items"])))}</small></span></a></li>'
        for slug, p in pubs.items())
    publishers = (f'<div class="xm-pubs"><h3>{esc(s["ext_pubs_heading"])}</h3><ul>{pub_cards}</ul></div>'
                  if pubs else '')
    return f'''<section class="page-intro xm-intro">
  <div class="wrap">
    {{{{crumbs}}}}
    <div class="xm-hero">
      <div>
        <h1>{esc(s["ext_section"])}</h1>
        <p class="lede">{esc(s["ext_lede"])}</p>
      </div>
      <ul class="xm-stats">{stats_html}</ul>
    </div>
    <form class="xm-search" role="search" action="extensions.html" method="get" data-xm-search>
      <label class="visually-hidden" for="xm-q">{esc(s["ext_search_label"])}</label>
      {{{{icon:search}}}}
      <input id="xm-q" type="search" name="q" placeholder="{esc(s["ext_search_placeholder"])}" autocomplete="off" spellcheck="false">
      <kbd aria-hidden="true">/</kbd>
    </form>
    <div class="xm-under">
      <div class="xm-chips" role="group" aria-label="{esc(s["ext_filter_category"])}" hidden>{"".join(chips)}</div>
      <a class="xm-flag" href="#about">{{{{icon:info}}}}{esc(s["ext_notice_title"])}</a>
    </div>
  </div>
</section>

<section class="band band--tight xm-band" id="browse">
  <div class="wrap xm-layout">
    <aside class="xm-side" id="xm-filters" aria-label="{esc(s["ext_filters"])}" hidden>
      <div class="xm-side-head"><h2>{esc(s["ext_filters"])}</h2><button type="button" class="xm-icon-btn" data-xm-close aria-label="{esc(s["js_close"])}">{{{{icon:x}}}}</button></div>
      {fieldset(s["ext_filter_type"], types)}
      {fieldset(s["ext_filter_price"], prices)}
      {fieldset(s["ext_filter_category"], cats)}
      {fieldset(s["ext_filter_source"], opened)}
      <fieldset class="xm-pub-filter"><legend>{esc(s["ext_filter_publisher"])}</legend><ul>{pub_opts}</ul>
        <button type="button" class="xm-more" data-xm-more hidden>{esc(s["ext_show_all"])}</button></fieldset>
      <div class="xm-side-foot"><button type="button" class="btn btn--ghost xm-clear" data-xm-clear>{esc(s["ext_clear"])}</button>
        <button type="button" class="btn btn--navy xm-apply" data-xm-close>{esc(s["ext_show_results"])}</button></div>
    </aside>
    <div class="xm-main">
      <div class="xm-bar" hidden>
        <button type="button" class="btn btn--ghost xm-filter-btn" aria-controls="xm-filters" aria-expanded="false">{{{{icon:sliders-horizontal}}}}{esc(s["ext_filters"])}<span class="xm-badge" hidden></span></button>
        <p class="xm-count" aria-live="polite" data-template="{esc(s["ext_showing"])}"></p>
        <label class="xm-sort"><span>{esc(s["ext_sort"])}</span><select data-xm-sort>{sorts}</select></label>
      </div>
      <div class="xm-active" hidden></div>
      {groups if entries else empty}
      <div class="xm-none" hidden><p><strong>{esc(s["ext_no_results"])}</strong><span>{esc(s["ext_no_results_d"])}</span></p>
        <button type="button" class="btn btn--ghost" data-xm-clear>{esc(s["ext_clear"])}</button></div>
    </div>
  </div>
</section>

<section class="band band--paper" id="about">
  <div class="wrap xm-about">
    <div>
      {ext_notice(s, " notice--big")}
      <p class="xm-official">{esc(s["ext_official"])} <a href="integrations.html">{esc(s["ext_official_integrations"])}</a> · <a href="themes.html">{esc(s["ext_official_themes"])}</a></p>
    </div>
    {publishers}
  </div>
</section>

{ext_add_section(s)}'''


def _crumb_meta(s, title):
    return f'<!--\ntitle: {title}\ndescription: {{desc}}\nsection: {s["ext_section"]}\nsection_url: extensions.html\ncta: no\n-->\n'


def ext_page(e, pubs, entries, s, code):
    """A generated listing page. Listing text stays in English; everything around it is localized."""
    esc = html.escape
    p = pubs[e['_pub']]
    paras = ''.join(f'<p>{esc(" ".join(x.split()))}</p>' for x in re.split(r'\n\s*\n', e['description']) if x.strip())
    by = esc(s['ext_by']).replace('{publisher}', f'<a href="{pub_page_name(p["slug"])}" lang="en">{esc(p["name"])}</a>')
    tags = ''.join(f'<li lang="en">{esc(t)}</li>' for t in e.get('tags', []))
    cover = ext_cover_file(e)
    shots = ([cover] if cover else []) + e.get('screenshots', [])  # the cover leads the gallery, full width
    gallery = ''
    if shots:
        figs = ''.join(
            f'<li{" class=is-cover" if cover and i == 0 else ""}><button type="button" class="xd-shot" data-shot="{i}" '
            f'aria-label="{esc(s["ext_screenshot"].replace("{n}", str(i + 1)))}">'
            f'<img src="{esc(src)}" alt="" width="1600" height="{800 if cover and i == 0 else 1000}" loading="{"eager" if i == 0 else "lazy"}"></button></li>'
            for i, src in enumerate(shots))
        gallery = (f'<ul class="xd-gallery xd-gallery--{min(len(shots) - bool(cover), 3)}" data-gallery>{figs}</ul>'
                   f'<dialog class="xd-lightbox" aria-label="{esc(s["ext_screenshots"])}"><img alt="">'
                   f'<button type="button" class="xm-icon-btn xd-lb-close" aria-label="{esc(s["js_close"])}">{{{{icon:x}}}}</button>'
                   f'<button type="button" class="xm-icon-btn xd-lb-prev" aria-label="{esc(s["carousel_prev"])}">{{{{icon:chevron-left}}}}</button>'
                   f'<button type="button" class="xm-icon-btn xd-lb-next" aria-label="{esc(s["carousel_next"])}">{{{{icon:chevron-right}}}}</button></dialog>')
    features = ''
    if e.get('features'):
        items = ''.join(f'<li>{esc(f)}</li>' for f in e['features'])
        features = f'<section class="xd-sec"><h2>{esc(s["ext_features"])}</h2><ul class="checklist" lang="en">{items}</ul></section>'
    english = f'<p class="note">{esc(s["ext_in_english"])}</p>' if code != 'en' else ''

    def link_btn(key, icon, label):
        return (f'<a class="xd-link" href="{esc(e[key])}" rel="ugc noopener">{{{{icon:{icon}}}}}<span>{esc(label)}</span>'
                f'<small lang="en">{esc(_host(e[key]))}</small></a>') if e.get(key) else ''
    links = ''.join([link_btn('demo_url', 'eye', s['ext_demo']), link_btn('docs_url', 'book-open', s['ext_docs']),
                     link_btn('support_url', 'life-buoy', s['ext_support']), link_btn('changelog_url', 'clock', s['ext_changelog']),
                     link_btn('source', 'code', s['ext_source_code'])])
    facts = [(s['ext_f_publisher'], f'<a href="{pub_page_name(p["slug"])}" lang="en">{esc(p["name"])}</a>'),
             (s['ext_f_type'], esc(s['ext_type_' + e['type']])),
             (s['ext_f_category'], esc(s['ext_cat_' + e['category']])),
             (s['ext_f_price'], esc(s['ext_price_' + e['price']])),
             (s['ext_f_license'], f'<span lang="en">{esc(e["license"])}</span>')]
    if e.get('version'):
        facts.append((s['ext_f_version'], f'<span lang="en">{esc(e["version"])}</span>'))
    facts += [(s['ext_f_requires'], f'<span lang="en">{esc(e["requires"])}</span>'),
              (s['ext_f_source'], (f'<a href="{esc(e["source"])}" rel="ugc noopener" lang="en">{esc(_host(e["source"]))}</a>'
                                   if e.get('source') else esc(s['ext_source_none']))),
              (s['ext_f_updated'], _date(e['updated']))]
    dl = ''.join(f'<div><dt>{esc(k)}</dt><dd>{v}</dd></div>' for k, v in facts)
    pub_desc = f'<p lang="en">{esc(p["description"])}</p>' if p.get('description') else ''
    pub_loc = f'<small>{{{{icon:map-pin}}}}<span lang="en">{esc(p["location"])}</span></small>' if p.get('location') else ''
    more = [x for x in p['items'] if x is not e]
    similar = [x for x in entries if x['category'] == e['category'] and x['_pub'] != e['_pub']][:4]
    more_html = ''
    if more:
        more_html += (f'<div class="band-head band-head--row"><div><h2>{esc(s["ext_more_from"]).replace("{publisher}", f"<span lang=en>{esc(p["name"])}</span>")}</h2></div>'
                      f'<a class="more" href="{pub_page_name(p["slug"])}">{esc(s["ext_view_all"])}</a></div>{ext_grid(more[:4], s)}')
    if similar:
        more_html += f'<div class="band-head xd-similar"><h2>{esc(s["ext_similar"])}</h2></div>{ext_grid(similar, s)}'
    report = (f'https://github.com/{{{{site_repo}}}}/issues/new?title='
              + re.sub(r'[^\w-]', lambda m: '%%%02X' % ord(m.group()), f'Listing: {e["name"]} ({e["slug"]})'))
    get_label = '<span>' + esc(s['ext_get']).replace('{publisher}', f'<span lang="en">{esc(p["name"])}</span>') + '</span>'
    sold = esc(s['ext_sold_by']).replace('{publisher}', f'<span lang="en">{esc(p["name"])}</span>')
    body = f'''<section class="page-intro xd-intro">
  {f'<div class="xd-bg ext-hue-{_hue(e["slug"])}" aria-hidden="true">{ext_pattern(e["slug"], 18, 8)}</div>'}
  <div class="wrap">
    {{{{crumbs}}}}
    <div class="xd-hero">
      <div class="xd-hero-main">
      <div class="xd-head">
        {ext_mark(e, "xl")}
        <div>
          <p class="xd-kicker">{esc(s["ext_cat_" + e["category"]])}</p>
          <h1 lang="en">{esc(e["name"])}</h1>
          <p class="xd-by">{by}{" · <span lang=en>v" + esc(e["version"]) + "</span>" if e.get("version") else ""} · {esc(s["ext_updated"]).replace("{date}", _date(e["updated"]))}</p>
        </div>
      </div>
      <p class="lede" lang="en">{esc(e["summary"])}</p>
      {f'<ul class="xd-tags">{tags}</ul>' if tags else ''}
      </div>
      <div class="xd-buy">
        {ext_price_badge(e, s, big=True)}
        <a class="btn btn--navy xd-get" href="{esc(e["url"])}" rel="ugc noopener" data-cta="extension-publisher">{get_label}{{{{icon:external-link}}}}</a>
        <p class="xd-sold">{sold}</p>
        {f'<div class="xd-links">{links}</div>' if links else ''}
      </div>
    </div>
  </div>
</section>

<section class="band band--tight xd-band">
  <div class="wrap xd-layout">
    <div class="xd-main">
      {gallery}
      <section class="xd-sec"><h2>{esc(s["ext_overview"])}</h2>{english}<div class="prose" lang="en">{paras}</div></section>
      {features}
      <section class="xd-sec"><h2>{esc(s["ext_details"])}</h2><dl class="xd-facts">{dl}</dl></section>
    </div>
    <aside class="xd-side">
      <div class="xd-box xd-pub">
        <a class="xd-pub-head" href="{pub_page_name(p["slug"])}">{pub_mark(p)}<span><strong lang="en">{esc(p["name"])}</strong>{pub_loc}</span></a>
        {pub_desc}
        <p class="xd-pub-links"><a href="{pub_page_name(p["slug"])}">{esc(pub_count(s, len(p["items"])))}</a><a href="{esc(p["url"])}" rel="ugc noopener" lang="en">{esc(_host(p["url"]))}</a></p>
      </div>
      {ext_notice(s, " notice--compact")}
      <a class="xd-report" href="{report}">{{{{icon:flag}}}}{esc(s["ext_report"])}</a>
    </aside>
  </div>
</section>
'''
    if more_html:
        body += f'<section class="band band--paper band--tight"><div class="wrap">{more_html}</div></section>\n'
    return _crumb_meta(s, e['name']).replace('{desc}', ' '.join(e['summary'].split())) + body


def pub_page(p, s):
    esc = html.escape
    items = p['items']
    n_mod = sum(1 for e in items if e['type'] == 'module')
    stats = [(len(items), s['ext_stat_listings']), (n_mod, s['ext_stat_modules']), (len(items) - n_mod, s['ext_stat_themes'])]
    stats_html = ''.join(f'<li><b>{n}</b><span>{esc(label)}</span></li>' for n, label in stats if n)
    groups = ''.join(
        f'<section class="xm-group"><div class="xm-group-head"><h3>{esc(s["ext_type_" + t + "s"])}</h3>'
        f'<span class="xm-group-n">{len(group)}</span></div>{ext_grid(group, s)}</section>'
        for t in EXT_TYPES
        for group in [sorted((e for e in items if e['type'] == t), key=lambda e: e['updated'], reverse=True)] if group)
    desc = p.get('description') or s['ext_pub_default'].replace('{publisher}', p['name'])
    meta = [f'<a href="{esc(p["url"])}" rel="ugc noopener">{{{{icon:globe}}}}<span lang="en">{esc(_host(p["url"]))}</span></a>']
    if p.get('location'):
        meta.append(f'<span>{{{{icon:map-pin}}}}<span lang="en">{esc(p["location"])}</span></span>')
    if p.get('support_url'):
        meta.append(f'<a href="{esc(p["support_url"])}" rel="ugc noopener">{{{{icon:life-buoy}}}}<span>{esc(s["ext_support"])}</span></a>')
    body = f'''<section class="page-intro xd-intro">
  <div class="wrap">
    {{{{crumbs}}}}
    <div class="xm-hero">
      <div class="xd-head">
        {pub_mark(p, "xl")}
        <div>
          <p class="xd-kicker">{esc(s["ext_publisher"])}</p>
          <h1 lang="en">{esc(p["name"])}</h1>
          <p class="xp-meta">{"".join(meta)}</p>
        </div>
      </div>
      <ul class="xm-stats">{stats_html}</ul>
    </div>
    <p class="lede"{' lang="en"' if p.get("description") else ""}>{esc(desc)}</p>
  </div>
</section>

<section class="band band--tight">
  <div class="wrap xp-body">
    <div class="band-head"><h2>{esc(s["ext_pub_listings"]).replace("{publisher}", f"<span lang=en>{esc(p['name'])}</span>")}</h2></div>
    {groups}
    <div class="xp-notice">{ext_notice(s, " notice--compact")}</div>
  </div>
</section>
'''
    return _crumb_meta(s, p['name']).replace('{desc}', ' '.join(desc.split())) + body


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
        items.append(f'<li><a href="{lang_base(c)}{target}" hreflang="{h}" lang="{h}" data-lang="{c}"{cur}>'
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


def lang_redirect():
    """English pages only: send a first-time visitor to their browser's language if the site has it.

    A language picked in the switcher is remembered (site.js, localStorage pnlcs-lang) and wins.
    Links inside the site never redirect, so choosing English stays English."""
    codes = {c: c for c, _, _ in LANGS}
    codes['pt'] = 'pt-br'
    return ('<script>(function(){try{var C=' + json.dumps(codes) + ',k=localStorage.getItem("pnlcs-lang"),t=null;'
            'if(k){t=k;}else if(!document.referrer||new URL(document.referrer).host!==location.host){'
            'var L=navigator.languages||[navigator.language||""];'
            'for(var i=0;i<L.length;i++){var l=(L[i]||"").toLowerCase();'
            'if(/^zh-(tw|hk|mo|hant)/.test(l))continue;'
            'var c=C[l]||C[l.split("-")[0]];if(c){t=c;break;}}}'
            'if(t&&t!=="en"&&C[t])location.replace("/"+t+location.pathname+location.search+location.hash);'
            '}catch(e){}})();</script>')


def og_image(code, name, generated):
    """Share image drawn by tools/og.py; the product screenshot until one exists."""
    rel = f'assets/og/{"x" if generated else code}/{name[:-5]}.jpg'
    return SITE_URL + (rel if (ROOT / rel).exists() else 'assets/img/client-hosting-tools.webp')


def read_localized(code, rel):
    """Translated file if it exists, otherwise the English source."""
    if code != 'en':
        f = SRC / 'i18n' / code / rel
        if f.exists():
            return f.read_text(), True
    return (SRC / rel).read_text(), code == 'en'


# The numbers in [data-stat] (stars, release, contributors …): site.js refreshes them in the browser, and what is
# written into the HTML is what a visitor sees when that fails (a network that blocks it, the GitHub API's 60 requests
# an hour per address used up). They come from shields.io at every build and are kept in data/stats.json, so a build
# without network still writes the last known numbers instead of ones typed in by hand.
STATS_SOURCES = {
    'stars': 'github/stars/Panelica/pnlcs', 'forks': 'github/forks/Panelica/pnlcs',
    'issues': 'github/issues/Panelica/pnlcs', 'release': 'github/v/release/Panelica/pnlcs',
    'contributors': 'github/contributors/Panelica/pnlcs', 'pulls': 'docker/pulls/panelica/pnlcs-runtime',
}


def project_stats():
    import urllib.request
    f = DATA / 'stats.json'
    stats = json.loads(f.read_text()) if f.exists() else {}
    if '--offline' in sys.argv:
        return stats
    fresh = {}
    for key, path in STATS_SOURCES.items():
        try:
            req = urllib.request.Request(f'https://img.shields.io/{path}.json', headers={'User-Agent': 'pnlcs.com build'})
            value = json.loads(urllib.request.urlopen(req, timeout=8).read())['value']
        except Exception:
            if not fresh:  # the first one failed: no network, do not wait for the rest
                print('note: shields.io not reachable, project numbers from data/stats.json')
                return stats
            continue
        if key == 'issues':
            value = value.split()[0]  # "3 open"
        if re.fullmatch(r'[\w.+-]{1,12}', value):
            fresh[key] = value
    if fresh and {k: v for k, v in stats.items() if k in fresh} != fresh:
        stats.update(fresh)
        f.write_text(json.dumps(dict(sorted(stats.items())), indent=2) + '\n')
    return stats


def fill_stats(doc, stats):
    return re.sub(r'(<[^>]*\bdata-stat="(\w+)"[^>]*>)([^<]*)(?=<)',
                  lambda m: m.group(1) + html.escape(stats.get(m.group(2), m.group(3))), doc)


def latest_title(code, latest, s):
    """The newest release title in the page language: src/i18n/<code>/releases.json maps a changelog slug to its
    translation. Until someone adds one, a translated page says "release notes of <date>" rather than English."""
    if code == 'en' or latest['version']:  # "PNLCS 1.16.0" reads the same in every language
        return inline(latest['title'])
    f = SRC / 'i18n' / code / 'releases.json'
    titles = json.loads(f.read_text()) if f.exists() else {}
    if latest['slug'] in titles:
        return html.escape(titles[latest['slug']])
    return html.escape(s['latest_generic']).replace('{date}', _date(latest['date']))


def build():
    layout = (SRC / 'layout.html').read_text()
    for asset in ('site.css', 'site.js'):  # cache-busting
        digest = hashlib.sha256((ROOT / 'assets' / asset).read_bytes()).hexdigest()[:10]
        layout = layout.replace(f'assets/{asset}"', f'assets/{asset}?v={digest}"')
    en_strings = json.loads((SRC / 'i18n' / 'strings.en.json').read_text())
    entries = changelog_entries()
    latest = entries[0]
    stats = project_stats()
    showcase = load_showcase()
    extensions = load_extensions()
    publishers = publisher_index(extensions, load_publishers())
    ext_pages = {ext_page_name(e): e for e in extensions}
    ext_pages.update({pub_page_name(slug): p for slug, p in publishers.items()})
    pages = sorted(p.name for p in (SRC / 'pages').glob('*.html'))
    clash = set(pages) & set(ext_pages)
    if clash:
        sys.exit(f'data/extensions.json: {sorted(clash)} would replace a site page')
    pages += sorted(ext_pages)

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
        offer, _ = read_localized(code, 'partials/offer.html')
        consent, _ = read_localized(code, 'partials/consent.html')
        js_strings = {k[3:]: v for k, v in s.items() if k.startswith('js_')}
        outdir = OUT if code == 'en' else OUT / code
        outdir.mkdir(parents=True, exist_ok=True)
        translated = 0

        for name in pages:
            if name in ext_pages:
                item = ext_pages[name]
                raw = (pub_page(item, s) if name.startswith('publisher-')
                       else ext_page(item, publishers, extensions, s, code))
                is_translated = True
            else:
                raw, is_translated = read_localized(code, f'pages/{name}')
            translated += is_translated
            meta, body = parse_page(raw)
            body = body.replace('{{whats_new}}', whats_new_html(entries, s, code))
            body = body.replace('{{showcase}}', '\n'.join(showcase_card(e, s) for e in showcase))
            body = body.replace('{{showcase_featured}}', showcase_carousel(showcase, s))
            body = body.replace('{{showcase_count}}', str(len(showcase)))
            body = body.replace('{{offer}}', offer)
            if '{{extensions_page}}' in body:
                body = body.replace('{{extensions_page}}', ext_browser(extensions, publishers, s))
            body = body.replace('{{web3forms_key}}', WEB3FORMS_KEY)
            if meta.get('cta', 'yes') != 'no':
                body += cta
            crumbs = ''
            if meta.get('section') or meta.get('crumbs') == 'short':  # short: home and the page, for a top-level menu item
                crumbs = (f'<nav class="crumbs" aria-label="{html.escape(s["breadcrumb"])}"><ol>'
                          f'<li><a href="./">{html.escape(s["home"])}</a></li>'
                          + ('' if not meta.get('section') else
                             f'<li><a href="{meta["section_url"]}">{html.escape(meta["section"])}</a></li>' if meta.get('section_url')
                             else f'<li>{html.escape(meta["section"])}</li>') +
                          f'<li aria-current="page">{html.escape(meta.get("heading", meta["title"]))}</li></ol></nav>')
            body = body.replace('{{crumbs}}', crumbs)
            title = meta['title'] if name == 'index.html' else f'{meta["title"]} | PNLCS'
            alternates = '\n'.join(f'<link rel="alternate" hreflang="{h}" href="{page_url(c, name)}">' for c, h, _ in LANGS)
            alternates += f'\n<link rel="alternate" hreflang="x-default" href="{page_url("en", name)}">'
            head_extra = alternates + f'\n<script>window.PNLCS_I18N={json.dumps(js_strings, ensure_ascii=False)};</script>'
            hdr = mark_current(header, name)
            if meta.get('section_url'):  # a listing or publisher page lights up its section in the menu
                hdr = hdr.replace(f'class="nav-link" href="{meta["section_url"]}"', f'class="nav-link" href="{meta["section_url"]}" aria-current="true"')
            hdr = hdr.replace('{{lang_switcher}}', lang_switcher(code, name, s))
            doc = (layout
                   .replace('<head>\n', '<head>\n' + (lang_redirect() + '\n' if code == 'en' else ''), 1)
                   .replace('<html lang="en">', f'<html lang="{hreflang}">')
                   .replace('{{title}}', html.escape(title))
                   .replace('{{description}}', html.escape(meta.get('description', '')))
                   .replace('{{url}}', page_url(code, name))
                   .replace('{{og_image}}', og_image(code, name, name in ext_pages))
                   .replace('{{head_extra}}', head_extra)
                   .replace('{{header}}', hdr)
                   .replace('{{footer}}', footer)
                   .replace('{{consent}}', consent)
                   .replace('{{content}}', body)
                   .replace('{{latest_title}}', latest_title(code, latest, s))
                   .replace('{{latest_slug}}', latest['slug'])
                   .replace('{{latest_date}}', html.escape(latest['date']))
                   .replace('{{site_repo}}', SITE_REPO))
            doc = re.sub(r'\{\{icon:([a-z0-9-]+)\}\}', lambda m: icon_html(m.group(1)), doc)
            doc = fill_stats(doc, stats)
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
    if not WEB3FORMS_KEY:
        print('warning: WEB3FORMS_KEY is empty, the discovery call form cannot send')
    print(f'built {len(pages)} pages x {len(LANGS)} languages into {OUT.relative_to(ROOT)}/  (translated: {", ".join(report)})')


if __name__ == '__main__':
    if '--refresh' in sys.argv:
        refresh()
    build()
