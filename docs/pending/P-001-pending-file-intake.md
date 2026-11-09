---
id: P-001
status: open
created: 2026-11-09
related: [P-002, P-003]
---

# Structured pending file as the intake of the analysis phase

## Problem
The owner's request reaches `impl-enrich` verbatim (`Request: <the owner's, verbatim>`), and the items the owner cites along the way (gaps, side issues, "also fix X") have no home before the report's Open items. Each run re-derives where the change goes from scratch, and nothing persists between runs. The owner wants the system to save, by default, every pending item the user cites into a pending file in a structured format, and that file to already be part of the analysis phase.

## Strategy
1. Define the pending-file format (title, problem, strategy, locations already identified, code references from CodeGraph and prompt-graph, other references, open questions). Draft: `docs/pending/README.md` § Format.
2. Give it a home per project: a new profile section (e.g. `_common § Pending`, default `docs/pending/`) so no skill cites a path; `/wh:profile` and `/wh:adopt` create it.
3. The structurer ([P-002](P-002-structurer-agent.md)) writes one file per pending item the user cites; the enricher's `analyze` stage reads it as input and starts from its Locations and Code references instead of from the raw request.
4. The enricher refines the file (confirms or corrects locations with `[code file:line]` certainty marks) and writes `ANALYSIS.md` from it; the pending file is the pre-processing of the enrich file, not a replacement for `ANALYSIS.md`.
5. At phase 6 (Close), items the run resolved are removed (or marked done) and items it left open are written back as pending files, replacing the "Open items" that today only live in the report.
6. Pre-fill the Code references deterministically: a script calls `prompt_graph.py --query "<title + problem>" --root .` and `codegraph explore` for the named symbols, so the model only validates them (rule of MANUAL § 7: deterministic steps go to scripts).

Alternative considered: keep using the report's Open items. Lost because the report is per run and is never read as input by the next run.

## Locations
- `plugins/wh/skills/implementation/SKILL.md:45-57` (§ 2 Enrich) — the analyze prompt passes the pending file path next to (or instead of) `Request:`.
- `plugins/wh/skills/implementation/SKILL.md:123-130` (§ 6 Close) — write back open items as pending files; delete resolved ones.
- `plugins/wh/agents/impl-enrich.md:17-44` (Stage `analyze`) — read the pending file first, confirm its locations, carry its title and strategy into `ANALYSIS.md`.
- `plugins/wh/skills/implementation/REPORT.md:23` (§ Open items) — point at the pending files instead of holding the items.
- `plugins/wh/skills/profile/COMMON.md` — new `## Pending` section (where the folder lives).
- `plugins/wh/skills/adopt/SKILL.md` and `plugins/wh/skills/adopt/scripts/check.py` — create and check the pending folder.
- `plugins/wh/skills/cleanup/SKILL.md` — "open items go to their home": the home becomes the pending folder.
- `docs/MANUAL.md` § 1 (pieces table), § 5 (source formats: add the pending format) — document it.
- `plugins/wh/.claude-plugin/plugin.json:3` — version bump (0.7.2 → next).

## Code references
- `resolve_symbols` `plugins/wh/scripts/prompt_graph.py:212` — symbol → `file:line` from the CodeGraph SQLite; reusable to fill Code references.
- `build_graph` `plugins/wh/scripts/prompt_graph.py:241` — glossary + features + symbols graph the query runs on.
- `main` `plugins/wh/scripts/prompt_graph.py:432` — `--query` / `--explain` CLI, entry point for the pre-fill script.
- `plugins/wh/skills/implementation/scripts/impl_env.sh:44-45` — creates `.impl/<slug>/`; would also copy or link the pending file in.
- `parse` `plugins/wh/skills/implementation/scripts/acceptance.py:24` — example of a deterministic markdown parser in the same style the pending parser would follow.

## Other references
- `docs/MANUAL.md` § 3 (prompt-graph: pointers only, lexical matching) and § 7 ("What is a script and what is the model").
- `plugins/wh/skills/implementation/TRIAGE.md` — plan format the enricher writes from the analysis.
- Visual flow of the current system: https://claude.ai/artifact/XNngkicGyKkWhEXV4UeQGi

## Open questions
- Folder name and place: `docs/pending/` in the project repo, or under `.claude/`?
- One file per item (this draft) or one file per run with many items?
- Does a pending file from a past run get picked up automatically by the next `/wh:implementation`, or only when the owner names it?
