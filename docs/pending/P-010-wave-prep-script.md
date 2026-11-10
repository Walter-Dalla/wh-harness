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
- `plugins/wh/skills/implementation/scripts/wave_prep.sh` (new) — new script [code plugins/wh/skills/implementation/scripts/acceptance.py:1]
- `plugins/wh/skills/implementation/LANES.md:34` (§ 2 Dispatch) — where the orchestrator sends `Stage: consult. WAVE W<n> at tip <hash>` before each wave after the first; the condition goes here [code plugins/wh/skills/implementation/LANES.md:34]
- `plugins/wh/agents/impl-enrich.md:59` (§ Stage `consult`, `WAVE W<n>` sentence) — what the enricher does with the message [code plugins/wh/agents/impl-enrich.md:59]
- `plugins/wh/skills/implementation/LANES.md:56` (§ 3, step 5) — `MAIN MOVED` list rides on the next `WAVE` message [code plugins/wh/skills/implementation/LANES.md:56]
- `plugins/wh/skills/implementation/scripts/scope.sh:15` — the `Owns:`/`May touch`/`Union:` reader the moved-files check reuses [code plugins/wh/skills/implementation/scripts/scope.sh:15]
- `SKILL.md` has no `WAVE` mention (grep): nothing changes there [code plugins/wh/skills/implementation/SKILL.md]
- `plugins/wh/skills/implementation/scripts/acceptance.py:85` — reused; line format `<id> · exit <n> · <command>` [code plugins/wh/skills/implementation/scripts/acceptance.py:85]
- `plugins/wh/skills/implementation/scripts/board.sh:15` — board line `<date> | <who> | <KIND> | <text>` the `CONTRACT` grep reads [code plugins/wh/skills/implementation/scripts/board.sh:15]
- `tests/test_scripts.py`, `docs/MANUAL.md:22`, `docs/MANUAL.md:387` — test and docs [code docs/MANUAL.md:387]

## Code references
- `acceptance.py` tests: `test_acceptance_runs_lane_items_and_logs` `tests/test_scripts.py:334` [code tests/test_scripts.py:334]

## Other references
- Owner's script backlog (2026-11-09).

## Open questions
- Exact `WAVE` protocol today in SKILL.md/LANES.md (who sends it, when) — enricher to locate. Located: `LANES.md:34` and `impl-enrich.md:59` (see Locations).
- At the tip every pending item is expected red (not done yet): what does "something came out red" mean as the trigger for calling the enricher?
