---
id: P-015
status: open
created: 2026-11-10
related: []
---

# SubagentStart hook calling prompt_graph.py --query, only if the event exists

## Problem
Owner: "Hook SubagentStart chamando prompt_graph.py --query: só se o evento existir comprovadamente; senão, descartar."
Today the `prompt-graph` hook is `UserPromptSubmit` only: it enriches the main session, never a subagent's prompt.

## Strategy
1. Prove the `SubagentStart` event exists (and that its output reaches the subagent's context) on the current Claude Code; if not proven, drop the item with the justification in the report.
2. If it exists: a `SubagentStart` entry in `hooks.json` calling `prompt_graph.py --query` for subagents (Explore/Plan would stop reading the whole glossary/index).
3. Version bump and MANUAL (hook changed).

## Locations
- `plugins/wh/hooks/hooks.json` — only `UserPromptSubmit` today [code plugins/wh/hooks/hooks.json:3]
- `plugins/wh/scripts/prompt_graph.py` (`--query` mode) — called by the new hook [code plugins/wh/scripts/prompt_graph.py:416]
- `docs/MANUAL.md:204` — states the hook is `UserPromptSubmit` and never enriches a subagent [code docs/MANUAL.md:204]
- `docs/MANUAL.md` § 3 (prompt-graph hook) — new event [code docs/MANUAL.md:63]
- `tests/test_prompt_graph.py` — test of the subagent input path [inferred]

## Code references
- `prompt_graph.py` root discovery loop `plugins/wh/scripts/prompt_graph.py:416` [code plugins/wh/scripts/prompt_graph.py:416]

## Other references
- Owner's script backlog (2026-11-09): "A verificar se o evento existe em 2.1.319".

## Open questions
- Does `SubagentStart` exist, what is its stdin payload (does it carry the subagent prompt?) and can its output add context? Proof required before any code.
