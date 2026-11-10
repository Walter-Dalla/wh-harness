---
id: P-008
status: open
created: 2026-11-10
related: [P-009, P-013, P-014]
---

# Parseable `## Commands` block in the implementation profile, validated by check.py

## Problem
Owner: "Bloco `## Commands` parseável no PROFILE de implementation (chaves fixas em backticks: build, suite, typecheck, service, health — ou alternativa melhor como commands.json), validado pelo check.py. Habilita lane_prompt.sh, profile_run.sh e new_names.py."
Today the profile's commands live in prose (§ Build, § Tests, § Checks, § Disposable service; ports in `_common § Ports`), so no script can run them.

## Strategy
1. Before implementing: validate against the current main (0.8.0, after run pending-intake) that the item still makes sense; if covered, obsolete or ill-posed, drop it with the justification in the report.
2. A parseable block in the implementation profile template with fixed keys in backticks: `build`, `suite`, `typecheck`, `service`, `health` — or a better alternative such as `.claude/profile/commands.json` (owner left the choice open).
3. `check.py` validates it.
4. It enables P-009 (`lane_prompt.sh`), P-013 (`profile_run.sh`) and P-014 (`new_names.py`).

## Locations
- `plugins/wh/skills/implementation/PROFILE.md` (§ Template, `##` sections from line 10) — new block or section [code plugins/wh/skills/implementation/PROFILE.md:5]
- `plugins/wh/skills/adopt/scripts/check.py` (`Check.profile`, `Check.profiles`) — validation of the block [code plugins/wh/skills/adopt/scripts/check.py:72]
- `.claude/profile/implementation.md` — this repo's own profile gets the block (protected file: owner reviews) [doc .claude/profile/implementation.md]
- `tests/test_adopt.py:48` (`test_demo_profiles_and_sources_are_ok_and_graph_builds`) and `:64` — the demo profile must stay `OK`; new check.py test of the block [code tests/test_adopt.py:48]
- `examples/demo/.claude/profile/implementation.md` — fixture gets the block, or `tests/test_adopt.py:48` goes red [code tests/test_adopt.py:50]
- `plugins/wh/skills/profile/SKILL.md:35` (§ 4 Write) — how the block is written [code plugins/wh/skills/profile/SKILL.md:35]
- `docs/MANUAL.md:36` (§ 2) and `:210` (§ 5) — document the block [code docs/MANUAL.md:210]

## Code references
- `Check.profile` `plugins/wh/skills/adopt/scripts/check.py:72` — compares profile `##` headings with the template's [code plugins/wh/skills/adopt/scripts/check.py:72]
- `template` `plugins/wh/skills/adopt/scripts/check.py:42` — reads the template's ```markdown block [code plugins/wh/skills/adopt/scripts/check.py:42]
- `LIMIT_SKILL` `plugins/wh/skills/adopt/scripts/check.py:20` — 60-line limit of a skill profile [code plugins/wh/skills/adopt/scripts/check.py:20]

## Other references
- Profile § Contract: a template section rename breaks existing profiles and `check.py`; producer and consumer change in the same plan.

## Open questions
- `## Commands` section with backticked keys, or `.claude/profile/commands.json`? (owner: "ou alternativa melhor")
- How do ports (`_common § Ports`, prose) reach the block — `service`/`health` keys, or a separate key?
