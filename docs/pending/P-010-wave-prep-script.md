---
id: P-010
status: open
created: 2026-11-10
related: []
---

# wave_prep.sh builds the WAVE message attachment; enricher only called when something is red

## Problem
Owner: "`wave_prep.sh`: anexo da mensagem WAVE ao enricher = acceptance.py + grep CONTRACT do board + git diff --name-status <base>..<tip>; enricher só é chamado se algo ficou vermelho."

## Strategy
1. Before implementing: validate against the current main (0.8.0); drop with justification in the report if covered, obsolete or ill-posed.
2. `wave_prep.sh` = `acceptance.py` + `grep CONTRACT` of the board + `git diff --name-status <base>..<tip>`.
3. The enricher is only called when something came out red.
4. Test in `tests/test_scripts.py`, cited in the skill, `docs/MANUAL.md` §1 table and §7.

## Locations
- `plugins/wh/skills/implementation/scripts/wave_prep.sh` — new script [inferred]
- `plugins/wh/skills/implementation/LANES.md:56` — today the `WAVE` message to the enricher (§2) carries the moved files [code plugins/wh/skills/implementation/LANES.md:56]
- `plugins/wh/skills/implementation/SKILL.md` (§ 2 Enrich / § 3 Execute) — where `WAVE` is sent; condition "only if red" [inferred]
- `plugins/wh/skills/implementation/scripts/acceptance.py` — reused [code docs/MANUAL.md:22]
- `plugins/wh/skills/implementation/scripts/board.sh` — board format the `CONTRACT` grep reads [code docs/MANUAL.md:22]
- `tests/test_scripts.py`, `docs/MANUAL.md:22`, `docs/MANUAL.md:387` — test and docs [code docs/MANUAL.md:387]

## Code references
- `acceptance.py` tests: `test_acceptance_runs_lane_items_and_logs` `tests/test_scripts.py:334` [code tests/test_scripts.py:334]

## Other references
- Owner's script backlog (2026-11-09).

## Open questions
- Exact `WAVE` protocol today in SKILL.md/LANES.md (who sends it, when) — enricher to locate.
