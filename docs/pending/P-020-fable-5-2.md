---
id: P-020
status: open
created: 2026-11-10
related: []
---

# Move the Fable model use from 5.1 to 5.2

## Problem
Owner: "Atualizar o uso do Fable 5.1 para Fable 5.2 (mais barato e mais potente): plugins/wh/agents/impl-enrich.md, plugins/wh/skills/adopt/templates/agents/Plan.md, plugins/wh/skills/implementation/SKILL.md, docs/MANUAL.md. Verificar se o alias `fable` já resolve para 5.2 (aí só documentar) ou se precisa fixar `claude-fable-5-2`; se o template Plan.md mudar, subir o marcador wh-template (e recopiar .claude/agents/Plan.md)."

## Strategy
1. Before implementing: validate against the current main (0.8.0); drop with justification in the report if not.
2. Check whether the `fable` alias already resolves to 5.2: if yes, only document; if not, pin `claude-fable-5-2`.
3. If the `Plan.md` template changes: bump its `wh-template` marker and recopy `.claude/agents/Plan.md`.

## Locations
- `plugins/wh/agents/impl-enrich.md:5` — `model: fable` [code plugins/wh/agents/impl-enrich.md:5]
- `plugins/wh/skills/adopt/templates/agents/Plan.md:5` — `model: fable`; marker `<!-- wh-template: plan 1 -->` at line 8 [code plugins/wh/skills/adopt/templates/agents/Plan.md:5]
- `.claude/agents/Plan.md:5` and `:8` — this repo's copy (`model: fable`, marker `plan 1`) [code .claude/agents/Plan.md:5]
- `plugins/wh/skills/implementation/SKILL.md:31` — enricher default `"fable"` [code plugins/wh/skills/implementation/SKILL.md:31]
- `docs/MANUAL.md:167` — `impl-enrich` on `fable` with `effort: medium` [code docs/MANUAL.md:167]
- `docs/MANUAL.md:204` — `Plan` on `fable` with `effort: medium` [code docs/MANUAL.md:204]
- `plugins/wh/skills/adopt/scripts/check.py` (`Check.agents`) — compares the marker numbers (`OUTDATED`) [code plugins/wh/skills/adopt/scripts/check.py:218]

## Code references
- `TEMPLATE_MARK` `plugins/wh/skills/adopt/scripts/check.py:27` — marker regex [code plugins/wh/skills/adopt/scripts/check.py:27]

## Other references
—

## Open questions
- Does the `fable` alias resolve to 5.2 on the installed Claude Code, and is `claude-fable-5-2` the exact model id? How to prove it (docs, `/model`, a run's transcript)?
