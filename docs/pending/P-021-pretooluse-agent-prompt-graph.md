---
id: P-021
status: open
created: 2026-11-10
related: [P-015]
---

# Enrich subagent prompts with prompt-graph through a PreToolUse hook on Agent

## Problem
P-015 (a `SubagentStart` hook calling `prompt_graph.py --query`) was dropped in run wh-pendencias: on Claude Code 2.1.322 the `SubagentStart` input carries only `agent_id` and `agent_type`, with no subagent prompt to match. Subagents (Explore, Plan, `impl-*`) still get no prompt-graph context unless the orchestrator pastes the block by hand.

## Strategy
1. Prove on a live session that a `PreToolUse` hook with matcher `Agent` receives `tool_input.prompt` and that `hookSpecificOutput.updatedInput` (or `additionalContext`) reaches the subagent; record the proof in `docs/MANUAL.md` § 8.
2. If proven: a `PreToolUse` entry in `plugins/wh/hooks/hooks.json` calling `prompt_graph.py` in a new mode that reads `tool_input.prompt` and appends the `[wh:prompt-graph]` block to it, skipping prompts that already carry one.
3. Test with a captured payload in `tests/test_prompt_graph.py`; version bump and MANUAL.
Alternative lost: `SubagentStart` (no prompt in its input).

## Locations
- `plugins/wh/hooks/hooks.json` — new `PreToolUse` entry, matcher `Agent`
- `plugins/wh/scripts/prompt_graph.py` (`main`) — new input mode for the Agent tool payload
- `docs/MANUAL.md` § 3 and § 8 — the event, and the SubagentStart finding it replaces
- `tests/test_prompt_graph.py` — payload test

## Code references
- `main` `plugins/wh/scripts/prompt_graph.py` — current `--query` and `UserPromptSubmit` branches [inferred]

## Other references
- Report `docs/reports/2026-11-10-wh-pendencias.md` (P-015 dropped); enricher analysis of that run (Claude Code 2.1.322 binary strings: `PreToolUse` input `tool_input`, output `updatedInput`).

## Open questions
- Does `updatedInput` on the Agent tool reach the subagent unchanged on the current Claude Code? Proof required before any code.
