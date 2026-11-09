---
id: P-005
status: open
created: 2026-11-09
related: [P-001]
---

# Pending ids are reused once landed files leave the folder

## Problem
`intake.sh <dir> --next` returns the highest `P-NNN` in the pending folder + 1. After run `pending-intake` removed P-001..P-004 (landed), `--next` printed `P-001` again: a new item would reuse an id that commits and reports already cite. Two concurrent branches can also take the same id (QA-wiring-02).

## Strategy
1. `--next` also scans `git log --all --name-only -- <pending dir>` (or a `.last-id` file in the folder) and returns the highest id ever seen + 1.
2. Test: a landed (removed) `P-004` still makes `--next` print `P-005`.

## Locations
- `plugins/wh/skills/implementation/scripts/intake.sh` (`--next` branch) — highest id ever seen.
- `tests/test_scripts.py` (`test_intake_*`) — removed-file case.

## Code references
- `plugins/wh/skills/implementation/scripts/intake.sh` — `--next` loop over `P-[0-9][0-9][0-9]*.md`.

## Other references
- `docs/reports/2026-11-09-pending-intake.md` § Open items.

## Open questions
- Git history scan or a counter file in the folder?
