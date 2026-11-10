---
id: P-017
status: open
created: 2026-11-10
related: []
---

# Accept .claude/perfil/ as alias of .claude/profile/, or document the rename

## Problem
Owner (play-store retro): "aceitar .claude/perfil/ como alias de .claude/profile/ (ou documentar o rename)."
Projects adopted before 0.7.0 may still have `.claude/perfil/`; every script reads `.claude/profile/` only. Enricher: 0.7.0 (commit 22ff861) renamed the folder and also `_comum.md` → `_common.md`, `contexto.json` → `context.json` and the `##` headings (Portuguese → English), so a folder alias alone would not read an old profile [code git show 22ff861 --stat].

## Strategy
1. Before implementing: validate against the current main (0.8.0); drop with justification in the report if not.
2. Either accept `.claude/perfil/` as an alias of `.claude/profile/`, or document the rename (owner left both open).

## Locations
- `docs/MANUAL.md:8` — says "the `.claude/profile/` folder did not change" since 0.7.0 [code docs/MANUAL.md:8]
- `plugins/wh/skills/adopt/scripts/check.py:19` (`PROFILE_DIR`) — profile folder [code plugins/wh/skills/adopt/scripts/check.py:19]
- `plugins/wh/scripts/prompt_graph.py:22` (`CONFIG`) — `context.json` path [code plugins/wh/scripts/prompt_graph.py:22]
- `plugins/wh/hooks/hooks.json:8` — hook looks for `.claude/profile/context.json` [code plugins/wh/hooks/hooks.json:8]
- `plugins/wh/skills/implementation/scripts/intake.sh:23` — `_common.md` path [code plugins/wh/skills/implementation/scripts/intake.sh:23]
- `plugins/wh/skills/implementation/scripts/impl_env.sh:57` — profile presence check [code plugins/wh/skills/implementation/scripts/impl_env.sh:57]
- `plugins/wh/skills/profile/SKILL.md:25` (§ 2 Sources) and `:39` (migration of the old skill) — where the old folder enters as a source and leaves [code plugins/wh/skills/profile/SKILL.md:25]
- `tests/test_adopt.py:41` — check.py test of the old folder [code tests/test_adopt.py:41]

## Code references
- `PROFILE_DIR` `plugins/wh/skills/adopt/scripts/check.py:19` [code plugins/wh/skills/adopt/scripts/check.py:19]
- `CONFIG` `plugins/wh/scripts/prompt_graph.py:22` [code plugins/wh/scripts/prompt_graph.py:22]

## Other references
- Play-store run retro (outside this repo) [inferred]. No `perfil` string anywhere in `plugins/` or `docs/MANUAL.md` today (grep).

## Open questions
- Alias (code in 5+ places, skills also cite `.claude/profile/` in prose) vs a documented rename plus a `check.py` WARN when `.claude/perfil/` exists?
