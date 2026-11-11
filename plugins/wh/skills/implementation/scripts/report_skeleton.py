#!/usr/bin/env python3
"""Skeleton of the /wh:implementation report from the board, the agent_chat/ files, the QA outputs and the retros.

    report_skeleton.py <slug> [--root <dir>] [--main <branch>] [--pr github|none] [--out <file>]

Reads only `<root>/.impl/<slug>/` (PLAN.md, BOARD.md, agent_chat/*.md, qa/*.md, retros/*.md); `--main` is accepted
for the call shape shared with the other run scripts and reads nothing. Prints the report with the `##` headings of
REPORT.md § Report, in order, to stdout or to `--out`. What the sources cannot give, and every missing source, is a
`TODO(orchestrator): …` line for the orchestrator to fill. The consolidated retro merges rows whose Category and
Proposal cells are equal after trimming (highest severity kept, Evidence joined as `<lane>: <evidence>` with ` / `),
sorted by severity (critical, high, medium, low, other) then first appearance. Exit 0; `REPORT_SKELETON FAILED:
<reason>` and exit 2 on a bad call or a missing `.impl/<slug>` folder.
"""
import glob
import os
import re
import sys

OPTIONS = ('--root', '--main', '--pr', '--out')
PR = {'github': 'PR on GitHub', 'none': 'no PR'}
QA_HEADER = '| Id | Type | Severity | Where | Evidence | Fix |'
RETRO_HEADER = '| # | Severity | Category | Evidence (lanes) | Proposal | Who applies |'
SEVERITY = ('critical', 'high', 'medium', 'low')
CHAT_TITLE = re.compile(r'^# Chat \S+ · (\S+) (\S+) · ')
QUESTION = re.compile(r'^## Question \((.*)\)\s*$')
ANSWER = re.compile(r'^## Answer \((.*?)\) · impact: (.*) · \S+\s*$')
CUT = 120


class Failed(Exception):
    pass


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
    if '--pr' in opts and opts['--pr'] not in PR:
        raise Failed('--pr takes github or none, not %s' % opts['--pr'])
    return rest[0], opts


def read(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return None


def cut(text):
    return text if len(text) <= CUT else text[:CUT] + '…'


def split_row(line):
    """Cells of a Markdown table row; a `|` inside backticks does not split."""
    cells, buf, tick = [], [], False
    for ch in line.strip()[1:-1] if line.strip().endswith('|') else line.strip()[1:]:
        if ch == '`':
            tick = not tick
        if ch == '|' and not tick:
            cells.append(''.join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    cells.append(''.join(buf).strip())
    return cells


def board_lines(text):
    """[(who, kind, text)] of the board lines `<date> | <who> | <KIND> | <text>`."""
    out = []
    for line in (text or '').splitlines():
        parts = line.split(' | ', 3)
        if len(parts) == 4:
            out.append((parts[1].strip(), parts[2].strip(), parts[3].strip()))
    return out


def first_line_after(lines, start):
    for line in lines[start + 1:]:
        if line.startswith('## '):
            return ''
        if line.strip():
            return line.strip()
    return ''


def consultation(path):
    lines = (read(path) or '').splitlines()
    title = CHAT_TITLE.match(lines[0]) if lines else None
    lane, item = (title.group(1), title.group(2)) if title else ('TODO(orchestrator): lane', 'item')
    question, answer = '', None
    for n, line in enumerate(lines):
        if QUESTION.match(line) and not question:
            question = first_line_after(lines, n)
        m = ANSWER.match(line)
        if m:
            answer = (first_line_after(lines, n), m.group(2).strip(), m.group(1).strip())
    if answer is None:
        return '%s %s · %s · unanswered' % (lane, item, cut(question))
    return '%s %s · %s · %s · impact %s · %s' % (lane, item, cut(question), cut(answer[0]), answer[1], answer[2])


def retro_rows(impl):
    """Merged retro rows, sorted by severity then first appearance."""
    merged, order = {}, []
    for path in sorted(glob.glob(os.path.join(impl, 'retros', '*.md'))):
        lane = os.path.splitext(os.path.basename(path))[0]
        for line in (read(path) or '').splitlines():
            if not line.startswith('|'):
                continue
            cells = split_row(line)
            if len(cells) != 6 or cells[0] == '#' or set(line.strip()) <= set('|-: '):
                continue
            _, severity, category, evidence, proposal, who = cells
            k = (category.strip(), proposal.strip())
            if k not in merged:
                merged[k] = {'severity': severity, 'category': category, 'evidence': [], 'proposal': proposal,
                             'who': who}
                order.append(k)
            row = merged[k]
            if rank(severity) < rank(row['severity']):
                row['severity'] = severity
            row['evidence'].append('%s: %s' % (lane, evidence))
    keys = sorted(order, key=lambda k: (rank(merged[k]['severity']), order.index(k)))
    return ['| %d | %s | %s | %s | %s | %s |' % (n, merged[k]['severity'], merged[k]['category'],
                                                   ' / '.join(merged[k]['evidence']), merged[k]['proposal'],
                                                   merged[k]['who']) for n, k in enumerate(keys, 1)]


def rank(severity):
    s = severity.strip().lower()
    return SEVERITY.index(s) if s in SEVERITY else len(SEVERITY)


def skeleton(slug, impl, pr):
    plan = read(os.path.join(impl, 'PLAN.md'))
    title = plan.splitlines()[0] if plan and plan.strip() else ''
    title = re.sub(r'^# ', '', title).strip() or 'TODO(orchestrator): title (no PLAN.md)'
    out = ['# %s · impl/%s · %s' % (title, slug, PR[pr] if pr else 'TODO(orchestrator): PR')]
    board_text = read(os.path.join(impl, 'BOARD.md'))
    board = board_lines(board_text)
    missing_board = 'TODO(orchestrator): no BOARD.md at %s' % os.path.join(impl, 'BOARD.md')
    out.append('Lanes:')
    ends = ['%s: %s' % (who, text) for who, kind, text in board if kind == 'END']
    out.extend(ends or [missing_board if board_text is None else 'TODO(orchestrator): no END line on the board'])

    out += ['', '## Errors']
    if board_text is None:
        out.append(missing_board)
    out.extend('%s: %s' % (who, text) for who, kind, text in board if kind == 'WARNING')
    out.append('TODO(orchestrator): test, check and lint failures, merge conflicts')

    out += ['', '## Open items']
    if board_text is None:
        out.append(missing_board)
    out.extend('%s: %s' % (who, text) for who, kind, text in board if kind == 'HUMAN')
    out.append('TODO(orchestrator): skipped items, decisions without the owner, → P-NNN')

    out += ['', '## Consultations']
    chat_dir = os.path.join(impl, 'agent_chat')
    chats = sorted(glob.glob(os.path.join(chat_dir, '*.md')))
    if not os.path.isdir(chat_dir):
        out.append('TODO(orchestrator): no agent_chat/ folder at %s' % chat_dir)
    out.extend(consultation(p) for p in chats)
    if os.path.isdir(chat_dir) and not chats:
        out.append('— (no consultation)')

    out += ['', '## QA']
    qa_dir = os.path.join(impl, 'qa')
    if not os.path.isdir(qa_dir):
        out.append('TODO(orchestrator): no qa/ folder at %s' % qa_dir)
    out += [QA_HEADER, '|---|---|---|---|---|---|']
    for path in sorted(glob.glob(os.path.join(qa_dir, '*.md'))):
        out.extend(line.rstrip() for line in (read(path) or '').splitlines() if line.startswith('| QA-'))
    out.append('TODO(orchestrator): fixed (commit) / retested / recorded')

    out += ['', '## Problems found', 'TODO(orchestrator): findings out of scope']

    out += ['', '## Consolidated retro']
    if not os.path.isdir(os.path.join(impl, 'retros')):
        out.append('TODO(orchestrator): no retros/ folder at %s' % os.path.join(impl, 'retros'))
    out += [RETRO_HEADER, '|---|---|---|---|---|---|'] + retro_rows(impl)
    return '\n'.join(out) + '\n'


def main(argv):
    try:
        slug, opts = parse_args(argv)
        impl = os.path.join(os.path.abspath(opts.get('--root', '.')), '.impl', slug)
        if not os.path.isdir(impl):
            raise Failed('%s does not exist' % impl)
        text = skeleton(slug, impl, opts.get('--pr'))
        if '--out' in opts:
            try:
                with open(opts['--out'], 'w', encoding='utf-8') as fh:
                    fh.write(text)
            except OSError as exc:
                raise Failed('cannot write %s: %s' % (opts['--out'], exc))
            print('WROTE %s' % os.path.abspath(opts['--out']))
        else:
            sys.stdout.write(text)
    except Failed as exc:
        print('REPORT_SKELETON FAILED: %s' % exc)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
