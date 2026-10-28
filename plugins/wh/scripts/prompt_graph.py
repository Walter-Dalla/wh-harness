#!/usr/bin/env python3
"""Hook UserPromptSubmit: enriquece o prompt com ponteiros do glossário, do mapa de features e do CodeGraph.

Determinístico e sem rede. O projeto declara as fontes em `.claude/perfil/contexto.json`; sem esse arquivo o hook
não faz nada. O grafo (termo -> feature -> símbolo) fica em cache em ~/.cache/walter-harness e só é refeito quando
uma fonte muda.

Uso manual:
  prompt_graph.py --query "texto" [--root DIR] [--explain]   # mostra o que seria injetado
  prompt_graph.py --build [--root DIR]                       # força a reconstrução do cache
"""
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys
import unicodedata

CONFIG = os.path.join('.claude', 'perfil', 'contexto.json')
CACHE_DIR = os.environ.get('WH_CACHE_DIR') or os.path.join(os.path.expanduser('~'), '.cache', 'walter-harness')
GRAPH_VERSION = 1
MAX_NGRAM = 5
DEFAULTS = {
    'glossario': 'docs/GLOSSARIO.md',
    'features': 'docs/features',
    'indice_features': 'docs/features/README.md',
    'codegraph': '.codegraph/codegraph.db',
    'class_name_globs': [],
    'max_features': 3,
    'max_termos': 4,
    'max_simbolos': 5,
    'min_score': 1.2,
    'max_interage': 6,
    'min_prompt': 12,
    'max_chars': 900,
    'idioma': 'pt',
}
LABELS = {
    'pt': {'head': 'Contexto determinístico (glossário + features + CodeGraph); só ponteiros, confira antes de afirmar.',
           'avoid': 'Evite "%s": o termo é %s (%s)', 'terms': 'Termos', 'read': 'Ler', 'near': 'Interage com',
           'symbols': 'Símbolos'},
    'en': {'head': 'Deterministic context (glossary + features + CodeGraph); pointers only, verify before asserting.',
           'avoid': 'Avoid "%s": the term is %s (%s)', 'terms': 'Terms', 'read': 'Read', 'near': 'Interacts with',
           'symbols': 'Symbols'},
}
# Nomes de seção aceitos (PT e EN); o contexto.json pode trocar por outros.
SECTIONS = {
    'simbolos': ['Símbolos de entrada', 'Entry symbols'],
    'interacoes': ['Interações', 'Interactions'],
    'armadilhas': ['Armadilhas', 'Pitfalls'],
}
# Peso de cada tipo de aresta alias -> feature.
W_KEYWORD, W_ALIAS, W_SYMBOL, W_GLOSS = 3.0, 3.0, 2.0, 1.0
KIND_RANK = {'class': 0, 'interface': 1, 'struct': 1, 'enum': 1, 'route': 2, 'method': 3, 'property': 4,
             'constant': 5, 'enum_member': 6, 'field': 6, 'function': 3}
BACKTICK = re.compile(r'`([^`]+)`')
IDENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_.]*$')


# ---------- normalização ----------

def _stem(tok):
    for suf, rep in (('oes', 'ao'), ('aes', 'ao'), ('ais', 'al'), ('eis', 'el'), ('ns', 'm')):
        if tok.endswith(suf) and len(tok) > len(suf) + 2:
            return tok[:-len(suf)] + rep
    if tok.endswith('s') and len(tok) > 3 and not tok.endswith('ss'):
        return tok[:-1]
    return tok


def tokens(text):
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c)).lower()
    return [_stem(t) for t in re.findall(r'[a-z0-9_]+', text)]


def key(text):
    return ' '.join(tokens(text))


def clean_md(text):
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    return re.sub(r'\*\*|__', '', text).strip()


# ---------- parse das fontes ----------

def split_row(line):
    cells, buf, tick = [], [], False
    for ch in line.strip().strip('|'):
        if ch == '`':
            tick = not tick
        if ch == '|' and not tick:
            cells.append(''.join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    cells.append(''.join(buf).strip())
    return cells


def split_keywords(cell):
    """Separa por vírgula e por parênteses, sem cortar o que está entre crases."""
    parts, buf, tick = [], [], False
    for ch in cell:
        if ch == '`':
            tick = not tick
        if not tick and ch in ',()':
            parts.append(''.join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append(''.join(buf))
    return parts


def business_aliases(cell):
    outside = re.sub(r'\([^)]*\)', ' ', cell)
    outside = re.sub(r'`[^`]*`', ' ', outside)
    parts = re.split(r'\s*/\s*|,\s*|\s+e\s+(?=[A-ZÀ-Ú])', outside)
    return [p for p in (re.sub(r'[^\w\s\-áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]', '', x).strip() for x in parts) if len(p) >= 3]


def code_aliases(cell):
    out = []
    for raw in BACKTICK.findall(cell):
        raw = raw.strip()
        if len(raw) >= 3 and (IDENT.match(raw) or raw.startswith(('GET ', 'POST ', 'PUT ', 'DELETE '))):
            out.append(raw)
    return out


def parse_glossary(path, pitfalls):
    entries, section = [], ''
    with open(path, encoding='utf-8') as fh:
        lines = fh.read().splitlines()
    sep = re.compile(r'^\|\s*:?-')
    for n, line in enumerate(lines):
        if line.startswith('## '):
            section = line[3:].strip()
            continue
        if not line.startswith('|') or sep.match(line):
            continue
        if n + 1 < len(lines) and sep.match(lines[n + 1]):
            continue  # cabeçalho da tabela
        cells = split_row(line)
        if len(cells) < 2:
            continue
        if any(section.startswith(t) for t in pitfalls):
            entries.append({'termo': clean_md(cells[1]), 'codigo': cells[0], 'evite': '',
                            'aliases': [[key(a), 'cod'] for a in code_aliases(cells[0])]})
            continue
        evite = cells[2] if len(cells) > 2 else ''
        aliases = [[key(a), 'neg'] for a in business_aliases(cells[0])]
        aliases += [[key(a), 'cod'] for a in code_aliases(cells[1])]
        aliases += [[key(a), 'evite'] for a in re.findall(r'"([^"]{3,40})"', evite)]
        entries.append({'termo': clean_md(cells[0]), 'codigo': cells[1], 'evite': evite,
                        'aliases': [a for a in aliases if a[0]]})
    return entries


def section(text, titles):
    for title in titles:
        m = re.search(r'^## ' + re.escape(title) + r'\s*$(.*?)(?=^## |\Z)', text, re.M | re.S)
        if m:
            return m.group(1)
    return ''


def parse_features(root, cfg):
    feat_dir = os.path.join(root, cfg['features'])
    feats = {}
    for path in sorted(glob.glob(os.path.join(feat_dir, '*.md'))):
        name = os.path.basename(path)
        if name.lower() == 'readme.md':
            continue
        with open(path, encoding='utf-8') as fh:
            text = fh.read()
        title = re.search(r'^# (.+)$', text, re.M)
        fm = re.search(r'^aliases:\s*\[(.*)\]\s*$', text, re.M)
        symbols = BACKTICK.findall(section(text, cfg['secoes']['simbolos']))
        links = re.findall(r'\]\(([\w\-]+\.md)\)', section(text, cfg['secoes']['interacoes']))
        feats[name] = {
            'path': os.path.relpath(path, root).replace(os.sep, '/'),
            'titulo': clean_md(title.group(1)) if title else name,
            'aliases': [a.strip() for a in fm.group(1).split(',')] if fm else [],
            'simbolos': [s for s in symbols if IDENT.match(s)],
            'interage': [l for l in dict.fromkeys(links) if l != name],
            'corpo': ' ' + key(text) + ' ',
            'keywords': [],
        }
    idx = os.path.join(root, cfg['indice_features'])
    if os.path.exists(idx):
        with open(idx, encoding='utf-8') as fh:
            for line in fh:
                m = re.match(r'^\|\s*\[([\w\-]+\.md)\]', line)
                if not m or m.group(1) not in feats:
                    continue
                cells = split_row(line)
                kws = []
                for cell in cells[1:]:
                    kws += [clean_md(k).strip('`').strip() for k in split_keywords(cell)]
                feats[m.group(1)]['keywords'] = [k for k in kws if len(k) >= 3]
    return feats


def resolve_symbols(root, cfg, names):
    found = {}
    db = os.path.join(root, cfg['codegraph'])
    if names and os.path.exists(db):
        try:
            con = sqlite3.connect('file:' + db + '?mode=ro', uri=True, timeout=1)
            rows = con.execute('SELECT name, kind, file_path, start_line FROM nodes WHERE name IN (%s)'
                               % ','.join('?' * len(names)), list(names)).fetchall()
            con.close()
        except sqlite3.Error:
            rows = []
        for name, kind, path, line in sorted(rows, key=lambda r: ('test' in r[2].lower(), KIND_RANK.get(r[1], 9), len(r[2]))):
            found.setdefault(name, '%s:%d' % (path, line))
    pattern = re.compile(r'^class_name\s+(\w+)', re.M)
    for g in cfg['class_name_globs']:
        for path in glob.glob(os.path.join(root, g), recursive=True):
            try:
                with open(path, encoding='utf-8') as fh:
                    head = fh.read(4000)
            except OSError:
                continue
            m = pattern.search(head)
            if m and m.group(1) in names:
                found.setdefault(m.group(1), os.path.relpath(path, root).replace(os.sep, '/') + ':1')
    return found


# ---------- grafo ----------

def build_graph(root, cfg):
    gloss_path = os.path.join(root, cfg['glossario'])
    entries = parse_glossary(gloss_path, cfg['secoes']['armadilhas']) if os.path.exists(gloss_path) else []
    feats = parse_features(root, cfg)
    index = {}  # chave -> [[tipo, id, peso]]

    def add(k, typ, ident, w):
        if k and len(k) >= 3:
            index.setdefault(k, []).append([typ, ident, w])

    for name, f in feats.items():
        for kw in f['keywords']:
            add(key(kw), 'f', name, W_KEYWORD)
        for a in f['aliases'] + [f['titulo']]:
            add(key(a), 'f', name, W_ALIAS)
        for s in f['simbolos']:
            add(key(s), 'f', name, W_SYMBOL)
    # Evite só vale quando a palavra não é termo próprio de outra linha.
    proper = {a[0] for e in entries for a in e['aliases'] if a[1] != 'evite'}
    gloss2feat = []
    for i, e in enumerate(entries):
        for k, kind in e['aliases']:
            if kind == 'evite' and k in proper:
                continue
            add(k, 'e' if kind == 'evite' else 'g', i, 1.0)
        keys = [k for k, kind in e['aliases'] if kind != 'evite']
        gloss2feat.append([n for n, f in feats.items() if any(' %s ' % k in f['corpo'] for k in keys)])
    symbols = {s for f in feats.values() for s in f['simbolos']}
    symbols |= {a for e in entries for a in code_aliases(e['codigo']) if IDENT.match(a)}
    for f in feats.values():
        del f['corpo']
    return {
        'version': GRAPH_VERSION,
        'glossario': [{'termo': e['termo'], 'codigo': e['codigo'], 'evite': e['evite']} for e in entries],
        'gloss2feat': gloss2feat,
        'features': feats,
        'index': index,
        'simbolos': resolve_symbols(root, cfg, symbols),
    }


def signature(root, cfg):
    paths = [os.path.join(root, CONFIG), os.path.join(root, cfg['glossario']), os.path.join(root, cfg['codegraph'])]
    paths += glob.glob(os.path.join(root, cfg['features'], '*.md'))
    parts = [str(GRAPH_VERSION), os.path.getmtime(__file__).__repr__()]
    for p in sorted(paths):
        try:
            st = os.stat(p)
            parts.append('%s:%d:%d' % (p, st.st_mtime_ns, st.st_size))
        except OSError:
            parts.append(p + ':-')
    return hashlib.sha1('|'.join(parts).encode()).hexdigest()


def load_graph(root, cfg, force=False):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache = os.path.join(CACHE_DIR, hashlib.sha1(root.encode()).hexdigest()[:16] + '.json')
    sig = signature(root, cfg)
    if not force and os.path.exists(cache):
        try:
            with open(cache, encoding='utf-8') as fh:
                data = json.load(fh)
            if data.get('sig') == sig:
                return data
        except (OSError, ValueError):
            pass
    data = build_graph(root, cfg)
    data['sig'] = sig
    tmp = cache + '.%d.tmp' % os.getpid()
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, cache)
    return data


# ---------- consulta ----------

def match(graph, prompt):
    toks = tokens(prompt)
    used = [False] * len(toks)
    hits = []
    for n in range(min(MAX_NGRAM, len(toks)), 0, -1):
        for i in range(len(toks) - n + 1):
            if any(used[i:i + n]):
                continue
            k = ' '.join(toks[i:i + n])
            if k in graph['index']:
                hits.append(k)
                for j in range(i, i + n):
                    used[j] = True
    return hits


def score(graph, hits):
    feats, terms, evites = {}, {}, {}
    for k in hits:
        targets = graph['index'][k]
        nfeat = sum(1 for t in targets if t[0] == 'f') or 1
        for typ, ident, w in targets:
            if typ == 'f':
                feats[ident] = feats.get(ident, 0) + w / nfeat
            elif typ == 'g':
                terms[ident] = terms.get(ident, 0) + 1
            elif typ == 'e':
                evites.setdefault(ident, k)
    for i in list(terms) + list(evites):
        linked = graph['gloss2feat'][i]
        for f in linked:
            feats[f] = feats.get(f, 0) + W_GLOSS / max(len(linked), 1)
    return feats, terms, evites


def short(text, n):
    text = re.sub(r'\s+', ' ', text).strip()
    return text if len(text) <= n else text[:n - 1].rstrip() + '…'


def render(graph, cfg, prompt, explain=False):
    hits = match(graph, prompt)
    feats, terms, evites = score(graph, hits)
    ranked = sorted(feats.items(), key=lambda kv: -kv[1])
    chosen = [f for f, s in ranked if s >= cfg['min_score']][:cfg['max_features']]
    gl = graph['glossario']
    lb = LABELS.get(cfg['idioma'], LABELS['pt'])
    lines = []
    for i, k in list(evites.items())[:2]:
        e = gl[i]
        lines.append(lb['avoid'] % (k, e['termo'], short(e['codigo'], 60)))
    term_ids = sorted(terms, key=lambda i: -terms[i])[:cfg['max_termos']]
    if term_ids:
        lines.append(lb['terms'] + ': ' + ' · '.join('%s = %s' % (short(re.sub(r'\s*\([^)]*\)', '', gl[i]['termo']), 40),
                                                       short(gl[i]['codigo'], 70))
                                             for i in term_ids))
    if chosen:
        fs = graph['features']
        lines.append(lb['read'] + ': ' + ' · '.join('%s (%s)' % (fs[f]['path'], short(fs[f]['titulo'], 45)) for f in chosen))
        near = [n for n in fs[chosen[0]]['interage'] if n not in chosen]
        if near:
            lines.append(lb['near'] + ': ' + ', '.join(n[:-3] for n in near[:cfg['max_interage']]))
    # Símbolo citado no prompt primeiro, depois os de entrada das features, alternando entre elas.
    cited = [s for s in graph['simbolos'] if key(s) in hits]
    queues = [list(graph['features'][f]['simbolos']) for f in chosen]
    order = cited + [q.pop(0) for _ in range(8) for q in queues if q]
    syms, seen = [], set()
    for s in order:
        if s in graph['simbolos'] and s not in seen:
            seen.add(s)
            syms.append('%s %s' % (s, graph['simbolos'][s]))
    if syms:
        lines.append(lb['symbols'] + ': ' + ' · '.join(syms[:cfg['max_simbolos']]))
    if not lines:
        out = ''
    else:
        out = '[wh:prompt-graph] ' + lb['head'] + '\n' + '\n'.join(lines)
        if len(out) > cfg['max_chars']:
            out = out[:cfg['max_chars'] - 1] + '…'
    if explain:
        sys.stderr.write('hits=%s\nfeatures=%s\n' % (hits, ranked[:8]))
    return out


# ---------- entrada ----------

def find_root(start):
    cur = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(cur, CONFIG)):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def load_cfg(root):
    cfg = dict(DEFAULTS)
    with open(os.path.join(root, CONFIG), encoding='utf-8') as fh:
        cfg.update(json.load(fh))
    cfg['secoes'] = dict(SECTIONS, **cfg.get('secoes', {}))
    return cfg


def main(argv):
    if '--build' in argv or '--query' in argv:
        rest = [a for a in argv[1:] if a not in ('--build', '--explain')]
        args = dict(zip(rest[0::2], rest[1::2]))
        root = find_root(args.get('--root', '.'))
        if not root:
            sys.exit('sem %s' % CONFIG)
        cfg = load_cfg(root)
        graph = load_graph(root, cfg, force='--build' in argv)
        if '--build' in argv:
            print('grafo: %d chaves, %d features, %d termos, %d símbolos' % (
                len(graph['index']), len(graph['features']), len(graph['glossario']), len(graph['simbolos'])))
        if '--query' in args:
            print(render(graph, cfg, args['--query'], explain='--explain' in argv))
        return
    if os.environ.get('WH_PROMPT_GRAPH') == '0':
        return
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return
    prompt = event.get('prompt') or ''
    root = find_root(event.get('cwd') or os.getcwd())
    if not root:
        return
    cfg = load_cfg(root)
    if len(prompt.strip()) < cfg['min_prompt']:
        return
    text = render(load_graph(root, cfg), cfg, prompt)
    if text:
        json.dump({'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext': text}}, sys.stdout,
                  ensure_ascii=False)


if __name__ == '__main__':
    try:
        main(sys.argv)
    except Exception as exc:  # hook nunca bloqueia o prompt
        if '--query' in sys.argv or '--build' in sys.argv:
            raise
        sys.stderr.write('prompt_graph: %s\n' % exc)
