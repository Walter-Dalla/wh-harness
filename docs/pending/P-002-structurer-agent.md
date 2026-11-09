---
id: P-002
status: open
created: 2026-11-09
related: [P-001, P-003]
---

# Structurer agent: a cheaper enricher that turns a raw request into pending files

## Problem
Today the expensive `impl-enrich` (`fable`) does everything from the raw request: understand what the owner asked, split it into items, locate the code and design the change. The first two are mechanical enough for a weaker model, and their output (the pending file of [P-001](P-001-pending-file-intake.md)) is what the enricher needs as input.

## Strategy
1. New agent `plugins/wh/agents/impl-structure.md` (name to decide), `model: opus`, tools `Read, Write, Bash, Skill`, runs in the clone without a worktree, writes only in the pending folder and `.impl/<slug>/`, never edits code.
2. Input: the raw request, the `[wh:prompt-graph]` block, the profile. Output: one pending file per item the user cited (title, problem, strategy as the user stated it, locations, code references), and an answer listing the files.
3. Locations and code references come from `codegraph explore` and the prompt-graph pointers, with the same certainty marks as the enricher (`[code file:line]`, `[doc file]`, `[inferred]`); it does not design the change: that stays with `impl-enrich`.
4. Its output is handed to `impl-enrich` (`fable`) in the analyze stage ([P-003](P-003-orchestrator-entry-modes.md)).
5. Model from profile § Models (new role "structurer"; no rule = `opus`), like the other roles.

Alternative considered: make the structuring a stage of `impl-enrich` (`Stage: structure`). Lost because the point is to run it on a cheaper model; one agent definition has one model in its frontmatter (the orchestrator can override `model` per call, which keeps this open).

## Locations
- `plugins/wh/agents/impl-structure.md` (new) — the agent.
- `plugins/wh/skills/implementation/SKILL.md:31` (Subagent model) — add the structurer role and its default.
- `plugins/wh/skills/implementation/SKILL.md:45-53` (§ 2 Enrich) — new step 0: dispatch the structurer when the request is unstructured.
- `plugins/wh/skills/implementation/PROFILE.md` (§ Models) — the structurer role in the template.
- `plugins/wh/skills/implementation/ENVIRONMENT.md:28-45` (§ Tools) — the structurer follows the same tool rules.
- `docs/MANUAL.md` § 1 (agents row) and § 7 (New agent) — document it.
- `plugins/wh/.claude-plugin/plugin.json:3` — version bump.

## Code references
- `main` `plugins/wh/scripts/prompt_graph.py:432` — `--query` gives the structurer the same pointers the hook gives the main session (subagents never receive the hook).
- `resolve_symbols` `plugins/wh/scripts/prompt_graph.py:212` — symbol → `file:line`.

## Other references
- `plugins/wh/agents/impl-enrich.md` — frontmatter (`model: fable`, `effort: medium`) and the certainty rule the structurer reuses.
- `docs/MANUAL.md` § 4, "Session model": the orchestrator pays 72–77% of the bill; moving work to cheaper agents is the stated direction.
- `docs/MANUAL.md` § 8: "The hook does not see a skill invoked by another skill".

## Open questions
- Name: `impl-structure`, `impl-intake` or `impl-triage`?
- Does the structurer ask the owner anything, or does every doubt wait for the enricher's `QUESTIONS`?
