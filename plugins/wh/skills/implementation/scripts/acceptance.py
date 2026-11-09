#!/usr/bin/env python3
"""Runs the Acceptance command of each item of a lane file or PLAN.md and reports the exit code, deterministically.

    acceptance.py <lane.md | PLAN.md> <worktree> [--only <id>[,<id>]] [--log <dir> --lane <name>] [--timeout <s>]

Lane file: a `## <id> · …` heading followed by `Acceptance: \`<command>\`` in its body. PLAN.md: a table row
`| <id> | … | \`<command>\` |` (the last backticked cell is the Acceptance). Each command runs with bash in the
worktree, stdout and stderr captured. Output, one line per item: `<id> · exit <n> · <command>`; with `--log`,
the output of each goes to `<dir>/<lane>-<id>.log` (the lane's Acceptance log the code QA reads). Final line:
`ACCEPTANCE: <green> green, <red> red, <skipped> without command`. Exit 0 after running (red is information:
red before the item, green after), 2 when the file has no item.
"""
import os
import re
import subprocess
import sys

HEADING = re.compile(r'^## +(\S+)')
ACCEPT = re.compile(r'Acceptance:\s*`([^`]+)`')
ROW = re.compile(r'^\|\s*([A-Za-z0-9_-]+-\d+)\s*\|(.*)\|\s*$')
TICK = re.compile(r'`([^`]+)`')


def parse(text):
    """[(id, command or None)] in file order; a lane heading without Acceptance gives None."""
    items, current = [], None
    for line in text.splitlines():
        m = ROW.match(line)
        if m and not line.startswith('| Id') and not set(line.strip()) <= set('|-: '):
            ticks = TICK.findall(m.group(2))
            items.append((m.group(1), ticks[-1] if ticks else None))
            continue
        m = HEADING.match(line)
        if m:
            current = m.group(1)
            items.append((current, None))
            continue
        m = ACCEPT.search(line)
        if m and current and items and items[-1][0] == current and items[-1][1] is None:
            items[-1] = (current, m.group(1).strip())
    return items


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
            items = parse(fh.read())
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
        try:
            p = subprocess.run(['bash', '-c', cmd], cwd=worktree, capture_output=True, text=True, timeout=timeout)
            code, out = p.returncode, p.stdout + p.stderr
        except subprocess.TimeoutExpired:
            code, out = 124, 'timeout after %ds\n' % timeout
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, '%s-%s.log' % (lane, ident)), 'w', encoding='utf-8') as fh:
                fh.write('$ %s\n%s\nexit %d\n' % (cmd, out, code))
        if code == 0:
            green += 1
        else:
            red += 1
        print('%s · exit %d · %s' % (ident, code, cmd))
    print('ACCEPTANCE: %d green, %d red, %d without command' % (green, red, skipped))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
