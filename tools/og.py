#!/usr/bin/env python3
"""Draw the 1200 × 630 share images (og:image) into assets/og/.

    python3 tools/og.py          # every page that has no image yet, or whose title changed
    python3 tools/og.py --all    # draw everything again

Needs Pillow and fonts that build.py does not: the Archivo variable TTF (OFL) and, for
Russian, Chinese and Japanese titles, the macOS system fonts below. Run it on a Mac after
changing a page title or description, then commit assets/og/. build.py uses an image when
it exists and falls back to the default one otherwise.

    assets/og/<lang>/<page>.jpg     site pages, one per language
    assets/og/x/<page>.jpg          listings and publishers (their text is English everywhere)
"""
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402

OUT = ROOT / 'assets' / 'og'
CACHE = Path.home() / '.cache' / 'pnlcs-og'
ARCHIVO_URL = 'https://github.com/google/fonts/raw/main/ofl/archivo/Archivo%5Bwdth,wght%5D.ttf'
FALLBACK = {  # Archivo has Latin only
    'ru': ('/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf', 0, '/System/Library/Fonts/Supplemental/Arial.ttf', 0),
    'zh': ('/System/Library/Fonts/Hiragino Sans GB.ttc', 2, '/System/Library/Fonts/Hiragino Sans GB.ttc', 0),
    'ja': ('/System/Library/Fonts/Hiragino Sans GB.ttc', 2, '/System/Library/Fonts/Hiragino Sans GB.ttc', 0),
}
W, H = 1200, 630
INK, NAVY, TEAL, WHITE, MUTED = '#141a31', '#405189', '#0ab39c', '#f8f9fd', '#aab2cc'
SHOT = ROOT / 'assets' / 'img' / 'hero-portal.webp'


def archivo():
    f = CACHE / 'Archivo.ttf'
    if not f.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        f.write_bytes(urllib.request.urlopen(ARCHIVO_URL).read())
    return f


def font(code, size, bold=True):
    if code in FALLBACK:
        path, idx, rpath, ridx = FALLBACK[code]
        return ImageFont.truetype(path if bold else rpath, size, index=idx if bold else ridx)
    f = ImageFont.truetype(str(archivo()), size)
    f.set_variation_by_axes([760 if bold else 440, 78 if bold else 100])
    return f


def wrap(draw, text, fnt, width, lines):
    """Greedy wrap; CJK text breaks between any two characters."""
    if re.search(r'[぀-ヿ一-鿿]', text):
        # one CJK character at a time, Latin words kept whole, no line starts with ー or punctuation
        tokens, joiner = re.findall(r'[A-Za-z0-9.-]+|\s+|.[ー、。，）」・]*', text), ''
    else:
        tokens, joiner = text.split(' '), ' '
    out, cur = [], ''
    for t in tokens:
        trial = (cur + joiner + t) if cur else t
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            out.append(cur.rstrip())
            cur = t.lstrip()
    out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        while draw.textlength(out[-1] + '…', font=fnt) > width:
            out[-1] = out[-1][:-1]
        out[-1] = out[-1].rstrip(' ,.;:') + '…'
    return out


def draw_card(code, kicker, title, desc, mark=None):
    img = Image.new('RGB', (W, H), INK)
    d = ImageDraw.Draw(img)
    # product screenshot bleeding off the right edge
    shot = Image.open(SHOT).convert('RGB')
    shot = shot.resize((760, int(760 * shot.height / shot.width)))
    mask = Image.new('L', shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, shot.width, shot.height), 14, fill=255)
    img.paste(shot, (720, 150), mask)
    fade = Image.new('L', (W, 1))
    for x in range(W):
        fade.putpixel((x, 0), 255 if x < 700 else max(0, 255 - (x - 700) * 255 // 240))
    img.paste(Image.new('RGB', (W, H), INK), (0, 0), fade.resize((W, H)))
    # logo
    lf = font('en', 40)
    d.text((72, 64), 'PNLCS', font=lf, fill=WHITE)
    lw = d.textlength('PNLCS', font=lf)
    d.ellipse((72 + lw + 6, 90, 72 + lw + 18, 102), fill=TEAL)
    y = 190
    if mark:
        d.rounded_rectangle((72, y, 72 + 84, y + 84), 18, fill='#e7eaf6')
        mf = font('en', 34)
        d.text((72 + 42, y + 42), mark, font=mf, fill=NAVY, anchor='mm')
        y += 110
    if kicker:
        d.text((72, y), kicker.upper(), font=font(code, 24), fill=TEAL)
        y += 44
    size = 74 if len(title) < 18 else 62 if len(title) < 34 else 50
    while True:  # a smaller size rather than a last line of one or two characters
        tf = font(code, size)
        lines = wrap(d, title, tf, 640, 3 if size < 60 else 2)
        if len(lines) == 1 or len(lines[-1].strip()) > 2 or size <= 44:
            break
        size -= 6
    for line in lines:
        d.text((72, y), line, font=tf, fill=WHITE)
        y += int(size * 1.08)
    y += 18
    df = font(code, 27, bold=False)
    for line in wrap(d, desc, df, 620, 2 if y < 440 else 1):
        d.text((72, y), line, font=df, fill=MUTED)
        y += 38
    d.text((72, H - 72), 'pnlcs.com', font=font('en', 26), fill=MUTED)
    return img


def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=80, optimize=True, progressive=True)


def main():
    redo = '--all' in sys.argv
    stamp_file = OUT / 'stamps.json'
    stamps = {} if redo or not stamp_file.exists() else json.loads(stamp_file.read_text())
    jobs = []
    en_strings = json.loads((build.SRC / 'i18n' / 'strings.en.json').read_text())
    for code, _, _ in build.LANGS:
        s = dict(en_strings)
        sf = build.SRC / 'i18n' / code / 'strings.json'
        if code != 'en' and sf.exists():
            s.update(json.loads(sf.read_text()))
        for page in sorted((build.SRC / 'pages').glob('*.html')):
            raw, _ = build.read_localized(code, f'pages/{page.name}')
            meta, _ = build.parse_page(raw)
            kicker = meta.get('section', '')
            jobs.append((OUT / code / page.name.replace('.html', '.jpg'), code, kicker, meta['title'], meta.get('description', ''), None))
    en = json.loads((build.SRC / 'i18n' / 'strings.en.json').read_text())
    entries = build.load_extensions()
    pubs = build.publisher_index(entries, build.load_publishers())
    for e in entries:
        kicker = f'{en["ext_cat_" + e["category"]]} · {e["publisher"]}'
        jobs.append((OUT / 'x' / build.ext_page_name(e).replace('.html', '.jpg'), 'en', kicker, e['name'], e['summary'],
                     build._monogram(e['name'])))
    for slug, p in pubs.items():
        jobs.append((OUT / 'x' / build.pub_page_name(slug).replace('.html', '.jpg'), 'en', en['ext_publisher'], p['name'],
                     p.get('description') or en['ext_pub_default'].replace('{publisher}', p['name']), build._monogram(p['name'])))
    drawn = 0
    for path, code, kicker, title, desc, mark in jobs:
        key = str(path.relative_to(OUT))
        digest = hashlib.sha256(json.dumps([code, kicker, title, desc, mark]).encode()).hexdigest()[:12]
        if stamps.get(key) == digest and path.exists():
            continue
        save(draw_card(code, kicker, title, desc, mark), path)
        stamps[key] = digest
        drawn += 1
    stamp_file.write_text(json.dumps(dict(sorted(stamps.items())), indent=0) + '\n')
    print(f'drew {drawn} of {len(jobs)} share images into {OUT.relative_to(ROOT)}/')


if __name__ == '__main__':
    main()
