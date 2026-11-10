#!/usr/bin/env python3
"""New identifiers of a diff that no glossary term covers: the candidate list of the code QA's name gate.

    new_names.py <diff file> <glossary | —>  |  new_names.py --range <base>...<ref> [--git <git path>] <glossary | —>

Rule: declared names only. New name: an identifier (3+ characters) DECLARED on an added line that appears on no
removed and no context line of the whole diff; first occurrence only, with the `+++ b/<path>` of its file and its
new-file line number. Declarations read: `def`/`class`/`fn`/`func` (also `func (r T) X`)/`function`/`const`/`let`
(`let mut`)/`var`/`interface`/`type`/`enum`/`struct`/`trait`/`record` followed by the name, after optional modifiers
(`export`, `public`, `pub`, `static`, `async`…); `X =`, `X: T =`, `self.X =`, `this.X =` and shell `X=` (also after
`local`/`export`/`readonly`/`declare`) at line start; shell `X() {`. Calls, keywords, builtins, parameters and words
inside strings are never names. Comment lines
(`#`, `//`, `/*`, `*`), trailing `#`/`//` comments and triple-quoted text are not read for new names; `.md` files
and lockfiles (package-lock.json, yarn.lock, pnpm-lock.yaml, poetry.lock, Cargo.lock, go.sum) are skipped. `--range` runs
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
COMMENT_LINE = re.compile(r'^\s*(#|//|/\*|\*/|\*\s|\*$)')
TRAILING_COMMENT = re.compile(r'\s(#|//)\s.*$')
TRIPLE = re.compile(r'"""|\'\'\'')
LOCKFILES = {'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', 'Cargo.lock', 'go.sum'}
MODIFIERS = (r'(?:(?:export|default|public|private|protected|internal|static|sealed|abstract|final|partial|readonly|'
             r'declare|async|unsafe|pub(?:\([^)]*\))?)\s+)*')
KEYWORD_DECL = re.compile(r'^\s*' + MODIFIERS + r'(?:def|class|function\*?|const|let(?:\s+mut)?|var|interface|type|'
                          r'enum|struct|trait|record|fn|func(?:\s*\([^)]*\))?)\s+([A-Za-z_]\w*)')
ASSIGN_DECL = re.compile(r'^\s*(?:(?:export|local|readonly|declare(?:\s+-\w+)?)\s+)?(?:self\.|this\.)?'
                         r'([A-Za-z_]\w*)(\s*)(?::\s*[^=]+?)?(\s*)=(?!=)')
SHELL_FUNC = re.compile(r'^\s*([A-Za-z_]\w*)\s*\(\)\s*\{')
NOT_A_NAME = {'else', 'try', 'finally', 'lambda', 'return', 'elif', 'while', 'for', 'if'}
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


def code_part(body, quote):
    """(code text of a new-side line, triple quote still open after it): comment lines, trailing `#`/`//`
    comments and triple-quoted text are dropped, so prose words of comments and docstrings are not names."""
    if quote is None and COMMENT_LINE.match(body):
        return '', None
    parts, pos = [], 0
    while True:
        if quote:
            end = body.find(quote, pos)
            if end < 0:
                return ' '.join(parts), quote
            pos, quote = end + 3, None
            continue
        m = TRIPLE.search(body, pos)
        if not m:
            parts.append(TRAILING_COMMENT.sub('', body[pos:]))
            return ' '.join(parts), None
        parts.append(body[pos:m.start()])
        quote, pos = m.group(0), m.end()


def declared(code):
    """Names declared on one line of code (see the module rule); a keyword argument on a continuation line is not."""
    m = KEYWORD_DECL.match(code) or SHELL_FUNC.match(code)
    if m:
        names = [m.group(1)]
    else:
        m = ASSIGN_DECL.match(code)
        if not m or m.group(1) in NOT_A_NAME:
            return []
        if not m.group(2) and not m.group(3) and code.rstrip().endswith((',', ')')):
            return []
        names = [m.group(1)]
    return [n for n in names if IDENT.fullmatch(n)]


def ignored(path):
    """Markdown files and lockfiles hold no code names."""
    return path.endswith('.md') or os.path.basename(path) in LOCKFILES


def new_names(diff):
    """[(path, line, name)] of the new identifiers, in diff order."""
    added, seen, old = [], set(), set()
    path, old_left, new_left, line_no, quote = '', 0, 0, 0, None
    old_path, skip = '', False
    for line in diff.splitlines():
        if old_left > 0 or new_left > 0:
            tag, body = line[:1], line[1:]
            if skip:
                if tag == '+':
                    new_left -= 1
                elif tag == '-':
                    old_left -= 1
                elif tag != '\\':
                    old_left -= 1
                    new_left -= 1
                continue
            if tag == '+':
                code, quote = code_part(body, quote)
                for name in declared(code):
                    if name not in seen:
                        seen.add(name)
                        added.append((path, line_no, name))
                new_left -= 1
                line_no += 1
            elif tag == '-':
                old.update(IDENT.findall(body))
                old_left -= 1
            elif tag != '\\':
                quote = code_part(body, quote)[1]
                old.update(IDENT.findall(body))
                old_left -= 1
                new_left -= 1
                line_no += 1
            continue
        if line.startswith('--- '):
            old_path = line[4:].strip()
            continue
        if line.startswith('+++ '):
            path = line[4:].strip()
            path = path[2:] if path.startswith('b/') else path
            quote = None
            skip = any(ignored(p) for p in (old_path, path) if p != '/dev/null')
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
                p = subprocess.run([git, 'diff', '--no-color', '--no-ext-diff', '--src-prefix=a/', '--dst-prefix=b/', rng],
                                   capture_output=True)
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
