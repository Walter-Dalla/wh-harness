---
id: P-013
status: open
created: 2026-11-10
related: [P-008]
---

# profile_run.sh runs the profile's build, suite and typecheck

## Problem
Owner: "`profile_run.sh <seção>`: build/suíte/typecheck do profile no fim de wave e QA final."
Blocked today by the commands being prose in the profile (P-008).

## Strategy
1. Before implementing: validate against the current main (0.8.0); drop with justification in the report if not.
2. `profile_run.sh <section>` runs build/suite/typecheck from the profile at end of wave and in the final QA.
3. Depends on P-008.
4. Test in `tests/test_scripts.py`, cited in the skill, `docs/MANUAL.md` §1 table and §7.

## Locations
- `plugins/wh/skills/implementation/scripts/profile_run.sh` — new script [inferred]
- `plugins/wh/skills/implementation/SKILL.md` (§ 3 Execute end of wave, § 5 Final QA line 102) — cite the script [code plugins/wh/skills/implementation/SKILL.md:102]
- `plugins/wh/skills/implementation/ENVIRONMENT.md:100` — exit-code rule of the suite command (pipe/pipefail) the script must honor [code plugins/wh/skills/implementation/ENVIRONMENT.md:100]
- `tests/test_scripts.py`, `docs/MANUAL.md:22`, `docs/MANUAL.md:387` — test and docs; shell script also through `bash -n` and `shellcheck` [code docs/MANUAL.md:387]

## Code references
—

## Other references
- Owner's script backlog (2026-11-09): "Bloqueado por comandos em prosa".

## Open questions
- `<section>` argument: profile section name or a key of the P-008 block?
