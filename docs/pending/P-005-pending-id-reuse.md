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
- `plugins/wh/skills/implementation/scripts/intake.sh:33` (`--next` branch, lines 33–42) — highest id ever seen: folder plus `git log --all --diff-filter=A` of the folder [code plugins/wh/skills/implementation/scripts/intake.sh:33]
- `tests/test_scripts.py:433` (`test_intake_resolves_ids_paths_no_argument_and_next`) — new test beside it, removed-file case [code tests/test_scripts.py:433]
- `plugins/wh/skills/implementation/ENVIRONMENT.md:20` (§ Scripts, `intake.sh` row) — `--next` wording [code plugins/wh/skills/implementation/ENVIRONMENT.md:20]

## Code references
- `plugins/wh/skills/implementation/scripts/intake.sh:35` — `--next` loop over `P-[0-9][0-9][0-9]*.md` [code plugins/wh/skills/implementation/scripts/intake.sh:35]. Measured 2026-11-10: a repo whose only file `P-004` was removed prints `P-001`; the history scan gives 004.

## Other references
- `docs/reports/2026-11-09-pending-intake.md` § Open items.

## Open questions
- Git history scan or a counter file in the folder?
