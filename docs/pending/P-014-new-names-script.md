---
id: P-014
status: open
created: 2026-11-10
related: [P-008]
---

# new_names.py lists new identifiers without a glossary term (QA gate 3 input)

## Problem
Owner: "`new_names.py <diff> <glossário>`: identificadores novos sem termo no glossário, entrada do gate 3 do QA."

## Strategy
1. Before implementing: validate against the current main (0.8.0); drop with justification in the report if not.
2. `new_names.py <diff> <glossary>` prints the new identifiers that have no glossary term.
3. Its output feeds QA gate 3 (Names).
4. Test in `tests/test_scripts.py`, cited in the skill/agent, `docs/MANUAL.md` §1 table and §7.

## Locations
- `plugins/wh/skills/implementation/scripts/new_names.py` — new script [inferred]
- `plugins/wh/agents/impl-qa.md:29` (gate 3 Names) — consumer of the output [code plugins/wh/agents/impl-qa.md:29]
- `plugins/wh/scripts/prompt_graph.py` — already parses the glossary (`context.json` `glossario`); candidate for reuse [code plugins/wh/scripts/prompt_graph.py:22]
- `tests/test_scripts.py`, `docs/MANUAL.md:22`, `docs/MANUAL.md:387` — test and docs [code docs/MANUAL.md:387]

## Code references
- `CONFIG` `plugins/wh/scripts/prompt_graph.py:22` — `.claude/profile/context.json`, source of the glossary path [code plugins/wh/scripts/prompt_graph.py:22]

## Other references
- Owner's script backlog (2026-11-09). Glossary format: `docs/MANUAL.md` § 5.1.

## Open questions
- Repo without glossary (this one has no `context.json`): script output and gate 3 behavior.
