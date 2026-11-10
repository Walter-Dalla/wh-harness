---
id: P-012
status: open
created: 2026-11-10
related: []
---

# report_skeleton.py writes the report skeleton from board, lanes, findings and retros

## Problem
Owner: "`report_skeleton.py <slug>`: esqueleto do relatório a partir de board, estados das lanes, tabelas de findings e retros (dedupe só por igualdade exata)."

## Strategy
1. Before implementing: validate against the current main (0.8.0); drop with justification in the report if not.
2. `report_skeleton.py <slug>` builds the skeleton from the board, lane states, findings tables and retros.
3. Dedupe only by exact equality.
4. Test in `tests/test_scripts.py`, cited in the skill, `docs/MANUAL.md` §1 table and §7.

## Locations
- `plugins/wh/skills/implementation/scripts/report_skeleton.py` (new) — new script [code plugins/wh/skills/implementation/scripts/acceptance.py:1]
- `plugins/wh/skills/implementation/REPORT.md:16` — report format the skeleton follows (template lines 16–38) [code plugins/wh/skills/implementation/REPORT.md:16]
- `plugins/wh/skills/implementation/ENVIRONMENT.md:16` (§ Scripts table) — new row [code plugins/wh/skills/implementation/ENVIRONMENT.md:16]
- `plugins/wh/skills/implementation/SKILL.md:128` (§ 6 Close, step 2 Report) — cites the script [code plugins/wh/skills/implementation/SKILL.md:128]
- `tests/test_scripts.py`, `docs/MANUAL.md:22`, `docs/MANUAL.md:387` — test and docs [code docs/MANUAL.md:387]

## Code references
—

## Other references
- Owner's script backlog (2026-11-09). Example report: `docs/reports/2026-11-09-pending-intake.md`.

## Open questions
—
