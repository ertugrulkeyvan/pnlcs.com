#!/usr/bin/env python3
"""Check translations against the English source.

    python3 tools/check_i18n.py            # every language
    python3 tools/check_i18n.py de fr      # only these

A translation may change text and a few human-readable attributes. Everything else
(tags, their order, classes, links, image paths, {{placeholders}}, code and commands,
front-matter keys) must be identical to the English file.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
TRANSLATABLE_ATTRS = {'alt', 'aria-label', 'title', 'data-alt', 'data-caption', 'content'}
FRONT_KEYS_TRANSLATED = {'title', 'description', 'section', 'heading'}


class Skeleton(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags, self.code, self._in_code = [], [], 0

    def handle_starttag(self, tag, attrs):
        kept = tuple(sorted((k, v) for k, v in attrs if k not in TRANSLATABLE_ATTRS))
        self.tags.append(('<', tag, kept))
        if tag in ('code', 'pre', 'kbd'):
            self._in_code += 1
            self.code.append('')

    def handle_endtag(self, tag):
        self.tags.append(('>', tag))
        if tag in ('code', 'pre', 'kbd') and self._in_code:
            self._in_code -= 1

    def handle_data(self, data):
        if self._in_code and self.code:
            self.code[-1] += data


def split_front(raw):
    m = re.match(r'<!--\n(.*?)\n-->\n', raw, re.S)
    if not m:
        return {}, raw
    meta = dict(line.partition(':')[::2] for line in m.group(1).splitlines())
    return {k.strip(): v.strip() for k, v in meta.items()}, raw[m.end():]


def compare(en_file, tr_file):
    problems = []
    en_meta, en_body = split_front(en_file.read_text())
    tr_meta, tr_body = split_front(tr_file.read_text())
    if set(en_meta) != set(tr_meta):
        problems.append(f'front-matter keys differ: {sorted(set(en_meta) ^ set(tr_meta))}')
    for k in en_meta:
        if k not in FRONT_KEYS_TRANSLATED and en_meta.get(k) != tr_meta.get(k):
            problems.append(f'front-matter "{k}" must not change')
    for k in FRONT_KEYS_TRANSLATED & set(en_meta):
        if not tr_meta.get(k):
            problems.append(f'front-matter "{k}" is empty')
    ph_en = sorted(re.findall(r'\{\{\w+\}\}', en_body))
    ph_tr = sorted(re.findall(r'\{\{\w+\}\}', tr_body))
    if ph_en != ph_tr:
        problems.append(f'placeholders differ: en={ph_en} tr={ph_tr}')
    a, b = Skeleton(), Skeleton()
    a.feed(en_body)
    b.feed(tr_body)
    if a.tags != b.tags:
        for i, (x, y) in enumerate(zip(a.tags, b.tags)):
            if x != y:
                problems.append(f'markup differs at tag #{i}: en={x} / tr={y}')
                break
        else:
            problems.append(f'tag count differs: en={len(a.tags)} tr={len(b.tags)}')
    if [c.strip() for c in a.code] != [c.strip() for c in b.code]:
        diff = [(x, y) for x, y in zip(a.code, b.code) if x.strip() != y.strip()][:3]
        problems.append(f'code/pre content changed: {diff}')
    if '—' in tr_body and '—' not in en_body:
        problems.append('em dash (—) added; use a comma, colon or parentheses')
    return problems


def main():
    langs = sys.argv[1:] or sorted(p.name for p in (SRC / 'i18n').iterdir() if p.is_dir())
    en_strings = json.loads((SRC / 'i18n' / 'strings.en.json').read_text())
    sources = sorted((SRC / 'pages').glob('*.html')) + sorted((SRC / 'partials').glob('*.html'))
    total = 0
    for code in langs:
        base = SRC / 'i18n' / code
        errors = []
        for en in sources:
            rel = en.relative_to(SRC)
            tr = base / rel
            if not tr.exists():
                errors.append(f'{rel}: missing')
                continue
            errors += [f'{rel}: {p}' for p in compare(en, tr)]
        sf = base / 'strings.json'
        if not sf.exists():
            errors.append('strings.json: missing')
        else:
            s = json.loads(sf.read_text())
            if set(s) != set(en_strings):
                errors.append(f'strings.json keys differ: {sorted(set(s) ^ set(en_strings))}')
            for k, v in en_strings.items():
                for ph in re.findall(r'\{\w+\}', v):
                    if ph not in s.get(k, ''):
                        errors.append(f'strings.json "{k}" lost placeholder {ph}')
        total += len(errors)
        print(f'[{code}] ' + ('OK' if not errors else f'{len(errors)} problem(s)'))
        for e in errors:
            print('   ', e)
    sys.exit(1 if total else 0)


if __name__ == '__main__':
    main()
