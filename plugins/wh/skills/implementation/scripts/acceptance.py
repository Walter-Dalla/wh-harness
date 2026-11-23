#!/usr/bin/env python3
r"""Runs the Acceptance command of each item of a lane file or PLAN.md and reports the exit code, deterministically.

    acceptance.py <lane.md | PLAN.md> <worktree> [--only <id>[,<id>]] [--log <dir> --lane <name>] [--timeout <s>]

Lane file: a `## <id> · …` heading followed by `Acceptance: \`<command>\`` in its body. PLAN.md: a table row
`| <id> | … | \`<command>\` |` (the last backticked cell is the Acceptance). An id is `<name>-<number>`
(`demo-3`, `QA-final-02`): any other `## ` heading (`## Notes`) is not an item. Lines inside a ``` fence are
not read (a `## ` example in a lane file is not an item). Each command runs with bash in the
worktree, stdout and stderr captured. Output, one line per item: `<id> · exit <n> · <command>`; with `--log`,
the output of each goes to `<dir>/<lane>-<id>.log` as the command writes it (the lane's Acceptance log the code
QA reads; a long command can be followed there while it runs). A green item whose command names a test file that
does not exist gets a second line, `<id> · WARNING · test file <path> does not exist: …`: several runners exit 0
when one of the files they were given is missing. Final line:
`ACCEPTANCE: <green> green, <red> red, <skipped> without command`. Exit 0 after running (red is information:
red before the item, green after), 2 when the file has no item or an unclosed fence.
"""
import os
import re
import shlex
import subprocess
import sys

HEADING = re.compile(r'^## ')
ITEM = re.compile(r'^## +([A-Za-z0-9_-]+-\d+)(?=\s|$)')
ACCEPT = re.compile(r'Acceptance:\s*`([^`]+)`')
ROW = re.compile(r'^\|\s*([A-Za-z0-9_-]+-\d+)\s*\|(.*)\|\s*$')
TICK = re.compile(r'`([^`]+)`')
TEST_FILE = re.compile(r'(?:^|/)(?:test_[^/]+|[^/]+[._-](?:test|spec)s?)\.[A-Za-z0-9]+$')
FILE_TEST = ('-f', '-e', '-s', '-r')


def parse(text):
    """[(id, command or None)] in file order; a lane heading without Acceptance gives None."""
    items, current, fenced = [], None, False
    for line in text.splitlines():
        if line.lstrip().startswith('```'):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = ROW.match(line)
        if m and not line.startswith('| Id') and not set(line.strip()) <= set('|-: '):
            ticks = TICK.findall(m.group(2))
            items.append((m.group(1), ticks[-1] if ticks else None))
            continue
        if HEADING.match(line):
            m = ITEM.match(line)
            current = m.group(1) if m else None  # a heading that is not an item ends the previous one
            if current:
                items.append((current, None))
            continue
        m = ACCEPT.search(line)
        if m and current and items and items[-1][0] == current and items[-1][1] is None:
            items[-1] = (current, m.group(1).strip())
    return items


def missing_test_files(cmd, worktree):
    """Test files the command names that are not in the worktree; one right after a file test (`test -f x`) is skipped."""
    try:
        words = shlex.split(cmd)
    except ValueError:
        words = cmd.split()
    out = []
    for i, word in enumerate(words):
        if word.startswith('-') or re.search(r'[*?\[\]${}=<>|&;()`]', word) or not TEST_FILE.search(word):
            continue
        if i and words[i - 1] in FILE_TEST:
            continue
        if not os.path.exists(os.path.join(worktree, word)) and word not in out:
            out.append(word)
    return out


def main(argv):
    if len(argv) < 3:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    path, worktree = argv[1], argv[2]
    args = dict(zip(argv[3::2], argv[4::2]))
    only = set(filter(None, args.get('--only', '').split(',')))
    log_dir, lane = args.get('--log'), args.get('--lane', os.path.splitext(os.path.basename(path))[0])
    timeout = int(args.get('--timeout', '600'))
    try:
        with open(path, encoding='utf-8') as fh:
            text = fh.read()
        if sum(1 for line in text.splitlines() if line.lstrip().startswith('```')) % 2:
            print('ACCEPTANCE FAILED: unclosed ``` fence in %s (the items after it would be skipped)' % path)
            return 2
        items = parse(text)
    except OSError as exc:
        print('ACCEPTANCE FAILED: %s' % exc)
        return 2
    if only:
        items = [it for it in items if it[0] in only]
    if not items:
        print('ACCEPTANCE FAILED: no item in %s' % path)
        return 2
    green = red = skipped = 0
    for ident, cmd in items:
        if not cmd:
            skipped += 1
            print('%s · no Acceptance command' % ident)
            continue
        missing = missing_test_files(cmd, worktree)  # before the run: the command may create the file
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            log = open(os.path.join(log_dir, '%s-%s.log' % (lane, ident)), 'w', encoding='utf-8')
            log.write('$ %s\n' % cmd)
            log.flush()
        else:
            log = None
        try:
            code = subprocess.run(['bash', '-c', cmd], cwd=worktree, stdout=log or subprocess.DEVNULL,
                                  stderr=subprocess.STDOUT, timeout=timeout).returncode
            tail = ''
        except subprocess.TimeoutExpired:
            code, tail = 124, 'timeout after %ds\n' % timeout
        if log:
            log.write('%s\nexit %d\n' % (tail, code))
            log.close()
        if code == 0:
            green += 1
        else:
            red += 1
        print('%s · exit %d · %s' % (ident, code, cmd))
        if code == 0:
            for missed in missing:
                print('%s · WARNING · test file %s does not exist: exit 0 may be the runner skipping it '
                      '(guard the command: test -f %s && …)' % (ident, missed, missed))
    print('ACCEPTANCE: %d green, %d red, %d without command' % (green, red, skipped))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
