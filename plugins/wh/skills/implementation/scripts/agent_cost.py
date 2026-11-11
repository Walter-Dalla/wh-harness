#!/usr/bin/env python3
"""Tokens per agent of one Claude Code session, read from its transcripts: who paid for a /wh:implementation run.

    agent_cost.py --session <id> [--cwd <dir>=.] [--projects <dir>=~/.claude/projects]

Reads `<projects>/<cwd, every non-alphanumeric character as ->/<id>.jsonl` (the main session: the orchestrator) and
`<id>/subagents/agent-*.jsonl` with their `.meta.json` (agent type and description). Read only. Each assistant message
counts once (the transcript repeats a message per content block; the last usage of a message id wins).
Prints a Markdown table, one row per agent, heaviest first:
`| Agent | Model | Requests | Input | Cache write | Cache read | Output | Share |`, then a `Total` row.
Share is the row's part of the weighted tokens (input ×1, cache write ×1.25, or ×2 for the part written with the
one-hour lifetime, cache read ×0.1, output ×5): the
price ratios inside one model. It is not dollars: models are priced differently, so read it beside the Model column.
Exit 0; `AGENT_COST FAILED: <reason>` and exit 2 on a bad call or a missing transcript.
"""
import glob
import json
import os
import re
import sys

OPTIONS = ('--session', '--cwd', '--projects')
FIELDS = ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens')
WEIGHTS = (1.0, 1.25, 0.1, 5.0)
LONG_WRITE_EXTRA = 0.75   # a one-hour cache write costs ×2, not ×1.25


class Failed(Exception):
    pass


def parse_args(argv):
    opts = {}
    i = 1
    while i < len(argv):
        if argv[i] not in OPTIONS or i + 1 >= len(argv):
            raise Failed('usage: ' + __doc__.strip().splitlines()[2].strip())
        opts[argv[i]] = argv[i + 1]
        i += 2
    if not re.fullmatch(r'[A-Za-z0-9-]+', opts.get('--session', '')):
        raise Failed('--session <id> is required (letters, digits and -)')
    return opts


def usage_of(path):
    """(requests, [input, cache write, cache read, output, 1h part of the cache write], most used model)."""
    seen = {}
    try:
        with open(path, encoding='utf-8', errors='replace') as fh:
            for line in fh:
                if '"usage"' not in line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                msg = entry.get('message')
                if entry.get('type') != 'assistant' or not isinstance(msg, dict) or not isinstance(msg.get('usage'), dict):
                    continue
                key = msg.get('id') or entry.get('requestId') or entry.get('uuid') or len(seen)
                usage = msg['usage']
                long_write = usage.get('cache_creation') if isinstance(usage.get('cache_creation'), dict) else {}
                seen[key] = (msg.get('model') or '?', [int(usage.get(f) or 0) for f in FIELDS]
                             + [int(long_write.get('ephemeral_1h_input_tokens') or 0)])
    except OSError as exc:
        raise Failed('cannot read %s: %s' % (path, exc))
    totals, models = [0, 0, 0, 0, 0], {}
    for model, counts in seen.values():
        if model == '<synthetic>':
            continue
        models[model] = models.get(model, 0) + 1
        totals = [a + b for a, b in zip(totals, counts)]
    model = max(models, key=models.get) if models else '—'
    return sum(models.values()), totals, model


def label_of(path):
    meta = {}
    try:
        with open(re.sub(r'\.jsonl$', '.meta.json', path), encoding='utf-8') as fh:
            meta = json.load(fh)
    except (OSError, ValueError):
        pass
    kind = meta.get('agentType') or os.path.basename(path)[len('agent-'):-len('.jsonl')]
    desc = (meta.get('description') or '').replace('|', '/').strip()
    return '%s · %s' % (kind, desc) if desc else kind


def weighted(counts):
    return sum(c * w for c, w in zip(counts, WEIGHTS)) + counts[4] * LONG_WRITE_EXTRA


def table(rows):
    total = [0, 0, 0, 0, 0]
    for _, _, _, counts in rows:
        total = [a + b for a, b in zip(total, counts)]
    whole = weighted(total) or 1.0
    out = ['| Agent | Model | Requests | Input | Cache write | Cache read | Output | Share |', '|---|---|---|---|---|---|---|---|']
    for label, model, requests, counts in sorted(rows, key=lambda r: -weighted(r[3])):
        out.append('| %s | %s | %d | %d | %d | %d | %d | %d%% |' % (label, model, requests, *counts[:4], round(100 * weighted(counts) / whole)))
    out.append('| Total | | %d | %d | %d | %d | %d | 100%% |' % (sum(r[2] for r in rows), *total[:4]))
    return out


def main(argv):
    try:
        opts = parse_args(argv)
        cwd = os.path.realpath(opts.get('--cwd', '.'))
        projects = os.path.expanduser(opts.get('--projects', os.path.join('~', '.claude', 'projects')))
        folder = os.path.join(projects, re.sub(r'[^A-Za-z0-9]', '-', cwd))
        main_path = os.path.join(folder, opts['--session'] + '.jsonl')
        if not os.path.isfile(main_path):
            raise Failed('no transcript at %s' % main_path)
        requests, counts, model = usage_of(main_path)
        rows = [('orchestrator (main session)', model, requests, counts)]
        for path in sorted(glob.glob(os.path.join(folder, opts['--session'], 'subagents', 'agent-*.jsonl'))):
            requests, counts, model = usage_of(path)
            if requests:
                rows.append((label_of(path), model, requests, counts))
    except Failed as exc:
        print('AGENT_COST FAILED: %s' % exc)
        return 2
    print('\n'.join(table(rows)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
