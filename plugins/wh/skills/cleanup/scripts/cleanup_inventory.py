#!/usr/bin/env python3
"""Inventory of a /wh:implementation run for /wh:cleanup: plan items x commits, old paths and old names cited in *.md.

    cleanup_inventory.py <slug> [--root <dir>] [--main <branch>] [--ref <ref>] [--plan <path>]

Defaults: `--root .`, `--main main`, `--ref impl/<slug>`, `--plan <root>/.impl/<slug>/PLAN.md`. Everything but the
plan is read from git objects at `<ref>` (no checkout). Four blocks, in this order, each heading always printed and
`—` on a block with nothing:

    ITEMS                 `<id> · <n> commit(s) · <short hashes>` or `<id> · NO COMMIT`, in plan order
    COMMITS WITHOUT ITEM  `<short hash> <subject>` of the non-merge commits of <main>..<ref> citing no plan id
    OLD PATHS             `<path> (D | R → <new path>) · <file.md>:<line> …` or `· not cited`
    OLD NAMES             `<name> · <file.md>:<line> …`, identifiers of removed non-.md lines that no tracked
                          non-.md file at <ref> holds any more and some *.md at <ref> still cites, sorted by name

Plan ids are the first cells `<letters, digits, - or _>-<number>` of the plan table rows; a commit counts for every
id that appears as a whole word in its subject. Exit 0 after printing; `CLEANUP_INVENTORY FAILED: <reason>` and
exit 2 on a bad call, a root that is not a git repository or an unknown ref.
"""
import os
import re
import subprocess
import sys

ROW = re.compile(r'^\|\s*([A-Za-z0-9_-]+-\d+)\s*\|')
NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]{3,}')
WORD = re.compile(r'[A-Za-z0-9_]+')
OPTIONS = ('--root', '--main', '--ref', '--plan')


class Failed(Exception):
    pass


def git(root, *args, ok=(0,)):
    p = subprocess.run(['git', '-C', root, *args], capture_output=True)
    if p.returncode not in ok:
        raise Failed('git %s: %s' % (' '.join(args), p.stderr.decode('utf-8', 'replace').strip()))
    return p.stdout.decode('utf-8', 'replace')


def parse_args(argv):
    rest, opts = [], {}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a.startswith('--'):
            if a not in OPTIONS or i + 1 >= len(argv):
                raise Failed('unknown option or option without value: %s' % a)
            opts[a] = argv[i + 1]
            i += 2
        else:
            rest.append(a)
            i += 1
    if len(rest) != 1:
        raise Failed('usage: ' + __doc__.strip().splitlines()[2].strip())
    return rest[0], opts


def plan_ids(path):
    """Plan row ids in order, without repeats; None when the plan file does not exist."""
    try:
        with open(path, encoding='utf-8') as fh:
            text = fh.read()
    except OSError:
        return None
    ids = []
    for line in text.splitlines():
        m = ROW.match(line)
        if m and m.group(1) not in ids:
            ids.append(m.group(1))
    return ids


def cites(ident, subject):
    return re.search(r'(?<![\w-])' + re.escape(ident) + r'(?![\w-])', subject) is not None


def read_blobs(root, ref, paths):
    """{path: text} of the files at <ref>, through one `git cat-file --batch` call."""
    if not paths:
        return {}
    data = ''.join('%s:%s\n' % (ref, p) for p in paths).encode('utf-8')
    p = subprocess.run(['git', '-C', root, 'cat-file', '--batch'], input=data, capture_output=True)
    if p.returncode != 0:
        raise Failed('git cat-file: %s' % p.stderr.decode('utf-8', 'replace').strip())
    out, pos, texts = p.stdout, 0, {}
    for path in paths:
        end = out.index(b'\n', pos)
        header = out[pos:end].split()
        pos = end + 1
        if len(header) < 3 or header[1] == b'missing':
            continue
        size = int(header[2])
        texts[path] = out[pos:pos + size].decode('utf-8', 'replace')
        pos += size + 1
    return texts


def items_block(ids, plan, commits):
    lines = ['ITEMS']
    if ids is None:
        lines.append('— (no plan at %s)' % plan)
    elif not ids:
        lines.append('—')
    for ident in ids or []:
        hashes = [h for h, s in commits if cites(ident, s)]
        if hashes:
            lines.append('%s · %d commit(s) · %s' % (ident, len(hashes), ' '.join(hashes)))
        else:
            lines.append('%s · NO COMMIT' % ident)
    lines.append('COMMITS WITHOUT ITEM')
    loose = ['%s %s' % (h, s) for h, s in commits if not any(cites(i, s) for i in ids or [])]
    lines.extend(loose or ['—'])
    return lines


def paths_block(root, ref, span):
    lines = ['OLD PATHS']
    for row in git(root, 'diff', '--no-color', '--no-ext-diff', '--name-status', '-M', span).splitlines():
        cells = row.split('\t')
        if cells[0] == 'D' and len(cells) == 2:
            old, label = cells[1], 'D'
        elif cells[0].startswith('R') and len(cells) == 3:
            old, label = cells[1], 'R → %s' % cells[2]
        else:
            continue
        found = git(root, 'grep', '--no-color', '-n', '-F', '-e', old, ref, '--', '*.md', ok=(0, 1))
        where = []
        for hit in found.splitlines():
            parts = hit[len(ref) + 1:].split(':', 2)
            if len(parts) == 3:
                where.append('%s:%s' % (parts[0], parts[1]))
        lines.append('%s (%s) · %s' % (old, label, ' '.join(where) if where else 'not cited'))
    if len(lines) == 1:
        lines.append('—')
    return lines


def removed_names(diff):
    """Identifiers on the removed lines of non-.md files of a unified diff."""
    names, path, old_left, new_left = set(), '', 0, 0
    for line in diff.splitlines():
        if old_left > 0 or new_left > 0:
            tag = line[:1]
            if tag == '-':
                old_left -= 1
                if not path.endswith('.md'):
                    names.update(NAME.findall(line[1:]))
            elif tag == '+':
                new_left -= 1
            elif tag != '\\':
                old_left -= 1
                new_left -= 1
            continue
        if line.startswith('--- '):
            path = line[4:].strip()
            path = path[2:] if path.startswith('a/') else path
        m = re.match(r'^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@', line)
        if m:
            old_left = 1 if m.group(1) is None else int(m.group(1))
            new_left = 1 if m.group(2) is None else int(m.group(2))
    return names


def names_block(root, ref, span):
    lines = ['OLD NAMES']
    candidates = removed_names(git(root, 'diff', '--no-color', '--no-ext-diff', '--src-prefix=a/', '--dst-prefix=b/',
                                   '-M', span))
    tracked = [p for p in git(root, 'ls-tree', '-r', '-z', '--name-only', ref).split('\0') if p]
    code = [p for p in tracked if not p.endswith('.md')]
    docs = [p for p in tracked if p.endswith('.md')]
    alive = set()
    for text in read_blobs(root, ref, code).values():
        alive.update(WORD.findall(text))
    gone = sorted(candidates - alive)
    if gone:
        doc_texts = read_blobs(root, ref, docs)
        for name in gone:
            pattern = re.compile(r'(?<![A-Za-z0-9_])' + re.escape(name) + r'(?![A-Za-z0-9_])')
            where = ['%s:%d' % (p, n) for p in docs if p in doc_texts
                     for n, text in enumerate(doc_texts[p].splitlines(), 1) if pattern.search(text)]
            if where:
                lines.append('%s · %s' % (name, ' '.join(where)))
    if len(lines) == 1:
        lines.append('—')
    return lines


def main(argv):
    try:
        slug, opts = parse_args(argv)
        root = os.path.abspath(opts.get('--root', '.'))
        main_branch = opts.get('--main', 'main')
        ref = opts.get('--ref', 'impl/%s' % slug)
        plan = opts.get('--plan', os.path.join(root, '.impl', slug, 'PLAN.md'))
        if not os.path.isdir(root):
            raise Failed('%s is not a folder' % root)
        git(root, 'rev-parse', '--git-dir')
        for r in (main_branch, ref):
            git(root, 'rev-parse', '--verify', '--quiet', r + '^{commit}')
        log = git(root, 'log', '--no-color', '--no-merges', '--reverse', '--format=%h %s', '%s..%s' % (main_branch, ref))
        commits = [tuple(line.split(' ', 1)) if ' ' in line else (line, '') for line in log.splitlines()]
        span = '%s...%s' % (main_branch, ref)
        out = items_block(plan_ids(plan), plan, commits) + paths_block(root, ref, span) + names_block(root, ref, span)
    except Failed as exc:
        print('CLEANUP_INVENTORY FAILED: %s' % exc)
        return 2
    print('\n'.join(out))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
