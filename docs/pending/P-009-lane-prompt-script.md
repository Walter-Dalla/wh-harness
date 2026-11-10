---
id: P-009
status: open
created: 2026-11-10
related: [P-008]
---

# lane_prompt.sh builds the lane/QA dispatch prompt and writes qa/<lane>.diff

## Problem
Owner: "`lane_prompt.sh <slug> <lane> [--qa]`: monta o prompt de dispatch de lane/QA (paths absolutos, hash, porta, remote) e grava qa/<lane>.diff."
Today the orchestrator assembles these prompts and the diff by hand, in Bash turns it pays for.

## Strategy
1. Before implementing: validate against the current main (0.8.0) that the item still makes sense; drop with justification in the report if not.
2. `lane_prompt.sh <slug> <lane> [--qa]` prints the dispatch prompt (absolute paths, hash, port, remote) and writes `qa/<lane>.diff`.
3. Test in `tests/test_scripts.py`, cited in the skill, `docs/MANUAL.md` §1 table and §7.
4. Depends on P-008 (ports and commands parseable).

## Locations
- `plugins/wh/skills/implementation/scripts/lane_prompt.sh` (new) — new script, beside `impl_env.sh` [code plugins/wh/skills/implementation/scripts/impl_env.sh:1]
- `plugins/wh/skills/implementation/LANES.md:22` — lane file header carries `port <n or —>`: the script reads the port there, so it does not depend on P-008 [code plugins/wh/skills/implementation/LANES.md:22]
- `plugins/wh/skills/implementation/ENVIRONMENT.md:16` (§ Scripts table) — new row [code plugins/wh/skills/implementation/ENVIRONMENT.md:16]
- `plugins/wh/skills/implementation/SKILL.md:85` (§ 4 Code QA) — today: "write the diff: `git -C <intwt> diff <base>...<remote>/<branch> > …/qa/<lane>.diff`"; QA prompt template at lines 87–94 [code plugins/wh/skills/implementation/SKILL.md:85]
- `plugins/wh/skills/implementation/SKILL.md:106` (§ 5 Final QA) — prompt template, lines 106–115 [code plugins/wh/skills/implementation/SKILL.md:106]
- `plugins/wh/skills/implementation/LANES.md:36` — lane dispatch prompt template, lines 36–44 (`Commands:` at 40) [code plugins/wh/skills/implementation/LANES.md:40]
- `tests/test_scripts.py` (`ScriptsTest`) — new test [code tests/test_scripts.py:42]
- `docs/MANUAL.md:22` (§1 table) and `docs/MANUAL.md:387` (§7) — script list [code docs/MANUAL.md:22]

## Code references
- `ScriptsTest` `tests/test_scripts.py:42` — home of script tests [code tests/test_scripts.py:42]

## Other references
- Owner's script backlog (2026-11-09 analysis): obstacle = ports in prose in `_common § Ports`.

## Open questions
- What does `<lane>` prompt need beyond what `impl_env.sh` already prints (fact sheet `KEY=VALUE`, profile § Contract)?
