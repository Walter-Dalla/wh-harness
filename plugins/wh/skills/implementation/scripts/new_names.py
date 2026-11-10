#!/usr/bin/env python3
"""New identifiers of a diff that no glossary term covers: the candidate list of the code QA's name gate.

    new_names.py <diff file> <glossary | —>  |  new_names.py --range <base>...<ref> [--git <git path>] <glossary | —>

New name: an identifier (3+ characters) on an added line that appears on no removed and no context line of the whole
diff; first occurrence only, with the `+++ b/<path>` of its file and its new-file line number. `--range` runs
`<git> diff <base>...<ref>` in the current directory. Covered: the identifier's normalized form, or any contiguous
run of its words (split at `_` and at lower-to-upper camelCase boundaries), equals a business or code alias of the
glossary, parsed by the hook's own `prompt_graph.parse_glossary`; a match with an Avoid alias does not cover and
adds ` · avoid → <term>`. Output: `NEW NAMES: <n> without a glossary term (of <m>)` (or `NO GLOSSARY: <m> new names`
when the glossary is `—` or does not exist), then `<path>:<line> <name>` in diff order, at most 200, then
`… <k> more`. The list is input for the QA's judgment, never a verdict. Exit 0; `NEW_NAMES FAILED: <reason>` and
exit 2 on a bad call, an unreadable diff or a failing git.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'scripts'))
import prompt_graph as pg  # noqa: E402

IDENT = re.compile(r'(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]{2,}')
HUNK = re.compile(r'^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
LIMIT = 200
NO_GLOSSARY = ('—', '-')


class Failed(Exception):
    pass


def parse_args(argv):
    args, rng, git = argv[1:], None, 'git'
    rest = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ('--range', '--git'):
            if i + 1 >= len(args):
                raise Failed('%s without value' % a)
            if a == '--range':
                rng = args[i + 1]
            else:
                git = args[i + 1]
            i += 2
        elif a.startswith('--'):
            raise Failed('unknown option %s' % a)
        else:
            rest.append(a)
            i += 1
    if (rng is None and len(rest) != 2) or (rng is not None and len(rest) != 1):
        raise Failed('usage: ' + __doc__.strip().splitlines()[2].strip())
    return rng, git, rest


def new_names(diff):
    """[(path, line, name)] of the new identifiers, in diff order."""
    added, seen, old = [], set(), set()
    path, old_left, new_left, line_no = '', 0, 0, 0
    for line in diff.splitlines():
        if old_left > 0 or new_left > 0:
            tag, body = line[:1], line[1:]
            if tag == '+':
                for name in IDENT.findall(body):
                    if name not in seen:
                        seen.add(name)
                        added.append((path, line_no, name))
                new_left -= 1
                line_no += 1
            elif tag == '-':
                old.update(IDENT.findall(body))
                old_left -= 1
            elif tag != '\\':
                old.update(IDENT.findall(body))
                old_left -= 1
                new_left -= 1
                line_no += 1
            continue
        if line.startswith('+++ '):
            path = line[4:].strip()
            path = path[2:] if path.startswith('b/') else path
            continue
        m = HUNK.match(line)
        if m:
            old_left = 1 if m.group(1) is None else int(m.group(1))
            new_left = 1 if m.group(3) is None else int(m.group(3))
            line_no = int(m.group(2))
    return [a for a in added if a[2] not in old]


def words(name):
    return [w for w in re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', name).replace('_', ' ').split() if w]


def glossary_index(path):
    """({covering alias key}, {avoid alias key: term})."""
    cover, avoid = set(), {}
    for entry in pg.parse_glossary(path, pg.SECTIONS['armadilhas']):
        for alias, kind in entry['aliases']:
            if kind in ('neg', 'cod'):
                cover.add(alias)
            elif kind == 'evite':
                avoid.setdefault(alias, entry['termo'])
    return cover, avoid


def keys(name):
    ws = words(name)
    out = [pg.key(name)]
    out += [pg.key(' '.join(ws[i:j])) for i in range(len(ws)) for j in range(i + 1, len(ws) + 1)]
    return out


def main(argv):
    try:
        rng, git, rest = parse_args(argv)
        glossary = rest[-1]
        if rng is None:
            try:
                with open(rest[0], encoding='utf-8', errors='replace') as fh:
                    diff = fh.read()
            except OSError as exc:
                raise Failed('cannot read the diff: %s' % exc)
        else:
            try:
                p = subprocess.run([git, 'diff', rng], capture_output=True)
            except OSError as exc:
                raise Failed('cannot run %s: %s' % (git, exc))
            if p.returncode != 0:
                raise Failed('%s diff %s: %s' % (git, rng, p.stderr.decode('utf-8', 'replace').strip()))
            diff = p.stdout.decode('utf-8', 'replace')
        names = new_names(diff)
        if glossary in NO_GLOSSARY or not os.path.isfile(glossary):
            head, listed = 'NO GLOSSARY: %d new names' % len(names), [(p, n, name, '') for p, n, name in names]
        else:
            cover, avoid = glossary_index(glossary)
            listed = []
            for p, n, name in names:
                ks = keys(name)
                bad = next((avoid[k] for k in ks if k in avoid), None)
                if bad is not None:
                    listed.append((p, n, name, ' · avoid → %s' % bad))
                elif not any(k in cover for k in ks):
                    listed.append((p, n, name, ''))
            head = 'NEW NAMES: %d without a glossary term (of %d)' % (len(listed), len(names))
    except Failed as exc:
        print('NEW_NAMES FAILED: %s' % exc)
        return 2
    print(head)
    for p, n, name, suffix in listed[:LIMIT]:
        print('%s:%d %s%s' % (p, n, name, suffix))
    if len(listed) > LIMIT:
        print('… %d more' % (len(listed) - LIMIT))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
