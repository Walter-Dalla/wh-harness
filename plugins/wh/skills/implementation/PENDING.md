# Pending file (intake of /wh:implementation)

One file per open item of the owner, `P-NNN-<slug>.md`, in the folder of `_common § Pending`. The structurer or the owner writes it, the enricher refines it, and it leaves the folder when it lands (the commit cites the id) or when the owner drops it.

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

## Who writes what
- **Structurer** (`impl-structure`): the owner's raw request → files, in the integration worktree; the orchestrator commits them.
- **Enricher**: confirms each line of Locations with `[code file:line]` and corrects the file in place.
- **Close step**: resolved files leave the folder; open items become new files numbered by `${CLAUDE_PLUGIN_ROOT}/skills/implementation/scripts/intake.sh <root> next`.
- **Owner**: by hand, any time.
