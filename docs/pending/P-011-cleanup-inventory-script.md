---
id: P-011
status: open
created: 2026-11-10
related: []
---

# cleanup_inventory.py lists commit ids against plan items and old names in *.md

## Problem
Owner: "`cleanup_inventory.py <slug>`: ids dos commits × itens do plano, git grep de nomes antigos em *.md (cleanup §1)."

## Strategy
1. Before implementing: validate against the current main (0.8.0); drop with justification in the report if not.
2. `cleanup_inventory.py <slug>`: commit ids × plan items; `git grep` of old names in `*.md`.
3. Test in `tests/test_scripts.py`, cited in the skill, `docs/MANUAL.md` §1 table and §7.

## Locations
- `plugins/wh/skills/cleanup/scripts/cleanup_inventory.py` (new; the folder is new too) — the consumer is `cleanup/SKILL.md` § 1, as `check.py` lives in `adopt/scripts/` [code plugins/wh/skills/cleanup/SKILL.md:15]
- `plugins/wh/skills/implementation/SKILL.md:130` (§ 6, step 4, inline minimum) — second consumer [code plugins/wh/skills/implementation/SKILL.md:130]
- `plugins/wh/skills/cleanup/SKILL.md:15` (§ 1 Inventory) — `git grep -n -e '<name>' -- '*.md'` per old name, line 18 [code plugins/wh/skills/cleanup/SKILL.md:18]
- `tests/test_scripts.py`, `docs/MANUAL.md:22`, `docs/MANUAL.md:387` — test and docs [code docs/MANUAL.md:387]

## Code references
—

## Other references
- Owner's script backlog (2026-11-09).

## Open questions
- Where do old names come from deterministically (diff of deleted/renamed symbols, CodeGraph)?
