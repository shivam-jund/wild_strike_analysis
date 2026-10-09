"""Stale-number sweep: numbers cited in a notebook's markdown that appear in no executed output/code of that notebook.
A screen, not a proof (derived figures, cross-references and outside facts are flagged too; words like "zero" are invisible to it)."""
import json, re, sys
NUM = re.compile(r'\d[\d,]*\.?\d*')

def _norm(raw):
    n = raw.rstrip('.,').replace(',', '')
    return n

def extract(text):
    nums = set()
    for m in NUM.finditer(text):
        n = _norm(m.group(0))
        if not n or re.fullmatch(r'\d', n) or re.fullmatch(r'(19|20)\d\d', n):
            continue
        nums.add(n)
        if re.fullmatch(r'\d+\.0+', n):        # 10000.0 also counts as 10000
            nums.add(n.split('.')[0])
    return nums

def src(c):
    s = c['source']
    return s if isinstance(s, str) else ''.join(s)

def known_numbers(nb):
    out_text, code_text = '', ''
    for c in nb['cells']:
        if c['cell_type'] != 'code':
            continue
        code_text += src(c) + '\n'
        for o in c.get('outputs', []):
            if o.get('output_type') == 'stream':
                out_text += o['text'] + '\n'
    return extract(out_text) | extract(code_text)

def matches_known(n, known):
    if n in known:
        return True
    if '.' in n:
        d = len(n.split('.')[1]); v = float(n)
        for k in known:
            if re.fullmatch(r'\d+\.\d+', k) and abs(float(k) - v) < 0.5 * 10 ** (-d) + 1e-9:
                return True
    return False

def sweep(path):
    nb = json.load(open(path, encoding='utf-8'))
    known = known_numbers(nb)
    flagged = []
    for i, c in enumerate(nb['cells']):
        if c['cell_type'] != 'markdown':
            continue
        text = src(c)
        for m in NUM.finditer(text):
            n = _norm(m.group(0))
            if not n or re.fullmatch(r'\d', n) or re.fullmatch(r'(19|20)\d\d', n) or matches_known(n, known):
                continue
            a, b = max(0, m.start() - 45), min(len(text), m.end() + 35)
            flagged.append((i, n, ' '.join(text[a:b].split())))
    return flagged

if __name__ == '__main__':
    for p in sys.argv[1:]:
        fl = sweep(p)
        print(f'=== {p}: {len(fl)} cited numbers matching nothing the notebook computed ===')
        for i, n, ctx in fl:
            print(f'  md[{i}] {n:>10}  ...{ctx}...')
