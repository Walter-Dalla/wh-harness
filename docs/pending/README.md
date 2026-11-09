# Pending

Gaps in the harness found by the owner, waiting to become work: one file per item, `P-NNN-<slug>.md`, in the format of [`plugins/wh/skills/implementation/PENDING.md`](../../plugins/wh/skills/implementation/PENDING.md) (copied below). `/wh:implementation P-NNN` runs one item, `/wh:implementation` with no argument runs every `status: open` item; an item leaves this folder when it lands (the commit cites the id) or when the owner drops it.

## Format

```markdown
---
id: P-NNN
status: open | in progress | dropped
created: YYYY-MM-DD
related: [P-NNN, …]
---

# <Title: what changes, in one line>

## Problem
What is missing or wrong today, and how it shows up. Owner's words when they exist.

## Strategy
The proposed direction, as numbered steps. Alternatives considered and why they lost, when there are any.

## Locations
Where the change happens, one line per place, each with its role in the change:
- `path:line` (§ Section) — what changes there

## Code references
Symbols the change touches or depends on, resolved by CodeGraph (`codegraph explore`) or the prompt-graph hook:
- `Symbol` `path:line` — role

## Other references
Docs, test-drive reports, runs, decisions that explain the item.

## Open questions
What the owner still decides, one `- <question>` per line; an answered one stays, as `- <question> → <answer> (owner, <date>)`. `—` when nothing.
```

