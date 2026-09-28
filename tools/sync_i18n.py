#!/usr/bin/env python3
"""Carry existing translations over to changed English pages.

    python3 tools/sync_i18n.py [REF] [--apply NEW.json]

REF (default HEAD) is a git revision where English and translations last matched
(tools/check_i18n.py passed there). From it, each language gets a dictionary
"English text -> translation", built by aligning the old English files with the old
translated files token by token. The current English files are then re-translated with
that dictionary into src/i18n/<lang>/.

Strings the dictionary does not know yet are written to tools/i18n-missing.json as
{"<lang>": {"<english>": ""}}. Fill in the translations and run again with
--apply tools/i18n-missing.json to put them in.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
ATTRS = ('alt', 'aria-label', 'title', 'data-alt', 'data-caption')
FRONT_KEYS = ('title', 'description', 'section', 'heading')
TOKEN = re.compile(r'(<!--.*?-->|<[^>]+>)', re.S)
ATTR = re.compile(r'\b(' + '|'.join(re.escape(a) for a in ATTRS) + r')="([^"]*)"')


def git_show(ref, rel):
    r = subprocess.run(['git', 'show', f'{ref}:{rel}'], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def split_front(raw):
    m = re.match(r'<!--\n(.*?)\n-->\n', raw, re.S)
    if not m:
        return None, raw
    return m.group(1), raw[m.end():]


def front_pairs(en_front, tr_front):
    en = dict(l.partition(':')[::2] for l in en_front.splitlines())
    tr = dict(l.partition(':')[::2] for l in tr_front.splitlines())
    return {en[k].strip(): tr[k].strip() for k in FRONT_KEYS if k in en and k in tr}


def learn(en_raw, tr_raw, table):
    """Add English->translation pairs from two structurally identical files."""
    ef, eb = split_front(en_raw)
    tf, tb = split_front(tr_raw)
    if ef and tf:
        table.update(front_pairs(ef, tf))
    et, tt = TOKEN.split(eb), TOKEN.split(tb)
    if len(et) != len(tt):
        return False
    for e, t in zip(et, tt):
        if e.startswith('<'):
            ea, ta = dict(ATTR.findall(e)), dict(ATTR.findall(t))
            for k, v in ea.items():
                if k in ta and v.strip():
                    table.setdefault(v, ta[k])
        elif e.strip():
            table.setdefault(e.strip(), t.strip())
    return True


def translate(en_raw, local, glob, missing):
    front, body = split_front(en_raw)
    out_front = None
    if front is not None:
        lines = []
        for line in front.splitlines():
            k, _, v = line.partition(':')
            v = v.strip()
            if k.strip() in FRONT_KEYS:
                t = local.get(v) or glob.get(v)
                if t is None:
                    missing.add(v)
                    t = v
                line = f'{k}: {t}'
            lines.append(line)
        out_front = '\n'.join(lines)
    parts, in_code = [], 0
    for tok in TOKEN.split(body):
        if tok.startswith('<'):
            name = re.match(r'</?\s*([a-zA-Z0-9]+)', tok)
            tag = name.group(1).lower() if name else ''
            if tag in ('code', 'pre', 'kbd'):
                in_code += -1 if tok.startswith('</') else 1

            def sub(m):
                v = m.group(2)
                if not v.strip():
                    return m.group(0)
                t = local.get(v) or glob.get(v)
                if t is None:
                    missing.add(v)
                    t = v
                return f'{m.group(1)}="{t}"'
            parts.append(ATTR.sub(sub, tok))
        elif tok.strip() and in_code <= 0:
            # {{placeholders}} (logos) are kept; only the words around them are looked up
            pieces = []
            for piece in re.split(r'(\{\{[\w:-]+\}\})', tok.strip()):
                s = piece.strip()
                if not s or re.fullmatch(r'\{\{[\w:-]+\}\}', s):
                    pieces.append(piece)
                    continue
                t = local.get(s) or glob.get(s)
                if t is None:
                    missing.add(s)
                    t = s
                pieces.append(piece.replace(s, t))
            t = ''.join(pieces)
            lead = tok[:len(tok) - len(tok.lstrip())]
            trail = tok[len(tok.rstrip()):]
            parts.append(lead + t + trail)
        else:
            parts.append(tok)
    body = ''.join(parts)
    return (f'<!--\n{out_front}\n-->\n' if out_front is not None else '') + body


def main():
    args = sys.argv[1:]
    extra = {}
    if '--apply' in args:
        i = args.index('--apply')
        extra = json.loads(Path(args[i + 1]).read_text())
        del args[i:i + 2]
    ref = args[0] if args else 'HEAD'
    langs = sorted(p.name for p in (SRC / 'i18n').iterdir() if p.is_dir())
    files = [p.relative_to(ROOT) for p in sorted((SRC / 'pages').glob('*.html')) + sorted((SRC / 'partials').glob('*.html'))]
    report = {}
    for lang in langs:
        tables, glob = {}, {}
        for rel in files:
            old_en = git_show(ref, str(rel))
            old_tr = git_show(ref, str(Path('src/i18n') / lang / rel.relative_to('src')))
            table = {}
            if old_en and old_tr and not learn(old_en, old_tr, table):
                print(f'[{lang}] {rel}: old files do not align, skipped')
            tables[str(rel)] = table
            for k, v in table.items():
                glob.setdefault(k, v)
        glob.update({k: v for k, v in extra.get(lang, {}).items() if v})
        missing = set()
        for rel in files:
            new_en = (ROOT / rel).read_text()
            out = translate(new_en, tables[str(rel)], glob, missing)
            dest = SRC / 'i18n' / lang / rel.relative_to('src')
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(out)
        report[lang] = {s: '' for s in sorted(missing)}
        print(f'[{lang}] {len(missing)} string(s) still in English')
    out = ROOT / 'tools' / 'i18n-missing.json'
    if any(report.values()):
        out.write_text(json.dumps(report, ensure_ascii=False, indent=1))
        print(f'wrote {out.relative_to(ROOT)}')
    elif out.exists():
        out.unlink()


if __name__ == '__main__':
    main()
