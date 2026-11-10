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
- `plugins/wh/skills/implementation/scripts/agent_chat.sh:26` (`ask`, numbering, lines 26–30) — `mkdir` lock, `NN` = highest prefix + 1 [code plugins/wh/skills/implementation/scripts/agent_chat.sh:26]
- `tests/test_scripts.py:483` (`test_agent_chat_creates_numbered_files_and_appends_answers`) — new test beside it: parallel case and held lock [code tests/test_scripts.py:483]

## Code references
- `plugins/wh/skills/implementation/scripts/agent_chat.sh:26` — `ask` numbering = count of files + 1 [code plugins/wh/skills/implementation/scripts/agent_chat.sh:26]. Only the orchestrator runs `ask` (plugins/wh/skills/implementation/ENVIRONMENT.md:23), so the race needs parallel Bash calls of one session, not two lanes. Measured 2026-11-10: 8 parallel `ask` gave 1–2 duplicated `NN` in 5 of 5 rounds.

## Other references
- `docs/reports/2026-11-09-pending-intake.md` § QA.

## Open questions
- Accept as cosmetic (numbers only order the files) instead of fixing?
