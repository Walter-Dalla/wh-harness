---
id: P-006
status: open
created: 2026-11-09
related: []
---

# agent_chat.sh numbers can collide between parallel lanes

## Problem
`agent_chat.sh ask` numbers a consultation as file count + 1. Two lanes asking at the same moment get the same `NN` with different `<lane>-<item>`, so the "already exists" guard does not fire and two files share a prefix (QA-scripts-01, low).

## Strategy
1. Take `NN` under a `mkdir`-based lock in `agent_chat/`, or retry when another `NN-*` appears after the write.
2. Test: two `ask` calls in parallel give different `NN`.

## Locations
- `plugins/wh/skills/implementation/scripts/agent_chat.sh` (`ask`, numbering) — lock or retry.
- `tests/test_scripts.py` — parallel case.

## Code references
- `plugins/wh/skills/implementation/scripts/agent_chat.sh` — `ask` numbering.

## Other references
- `docs/reports/2026-11-09-pending-intake.md` § QA.

## Open questions
- Accept as cosmetic (numbers only order the files) instead of fixing?
