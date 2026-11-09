---
id: P-004
status: open
created: 2026-11-09
related: [P-001]
---

# Persist the consultations between impl-dev, orchestrator and impl-enrich

## Problem
A consultation travels only through `SendMessage`: `impl-dev` (or `impl-qa`) → `QUESTION <lane> <item>: …` → orchestrator → `Stage: consult.` → `impl-enrich` → answer with impact → orchestrator → asker. The exchange itself is written nowhere; it lives in the context of the three agents. What reaches disk is only a side effect, and only in some cases:

| What | Persisted? | Where |
|---|---|---|
| The question text | no (only while pending) | `progress/<lane>.md` `Open:` line, rewritten on the next item |
| Answer `go on` / `adjust` limited to the item | no | asker's context only |
| Answer whose adjustment goes beyond the item | yes, as the result | `ANALYSIS.md` and lane files (enricher updates them) |
| Impact `contract` / `other lanes` | partly | board `CONTRACT` line, updated lane files |
| `OWNER:` followed without asking | yes | report's Open items |
| QA objection | yes | QA output (`Record the objection with its answer`) |
| Answer given by the orchestrator after a session restart | yes | `PLAN.md` Decisions, "orchestrator decision" |

Consequences: a continuation agent (LANES.md §3 step 9) and the QA cannot see why the code diverges from the lane file when the answer was item-scoped; after a session restart the enricher is dead and its reasoning is lost; the report and the retros cannot audit the decisions taken mid-run; and `.impl/<slug>/` is deleted at cleanup, so even what was written is gone unless the report copied it.

## Strategy
1. One file per consultation, `<root>/.impl/<slug>/consults/<NN>-<lane>-<item>.md`: question, context, proposal, answer, impact, who answered (enricher / orchestrator from the plan / owner). Created by a script so the numbering and timestamps are deterministic (same reasoning as `board.sh`).
2. The asker writes nothing new: the orchestrator records the question when it relays it, and the answerer (enricher, or the orchestrator answering from the plan) records the answer in the same file. The `SendMessage` back carries the file path.
3. Board: one `CONSULT` line per consultation (`<lane> <item> → <impact> · consults/NN…`), via `board.sh`, so the board stays the timeline.
4. Checkpoint: `Open:` cites the consult file instead of copying the question; continuation agents read the consult files of their lane.
5. QA (`code` and `final`) reads the consult files of the lane as part of "intent before code".
6. Close: the report gets a "Consultations" section (one line each: question, answer, impact), so the trail survives the cleanup of `.impl/`. With [P-001](P-001-pending-file-intake.md), consultations that ended in `OWNER:` or `replan` also become pending files.

Alternative considered: a single `CONSULTS.md` append-only like the board. Viable and simpler; per-file wins only if answers get long (sketches, file lists).

## Locations
- `plugins/wh/skills/implementation/SKILL.md:55` (§ 2, "Consultations during the task") — record question and answer, path in the relay.
- `plugins/wh/skills/implementation/LANES.md:48` (Question bridge) and `:52` (`WAITING`) — same rule for lanes.
- `plugins/wh/agents/impl-enrich.md:57-58` (Stage `consult`) — write the answer into the consult file.
- `plugins/wh/agents/impl-dev.md` (§ Doubts: consult the enricher) — read the answer from the file on continuation.
- `plugins/wh/agents/impl-qa.md:38` — the objection goes through the same file.
- `plugins/wh/skills/implementation/ENVIRONMENT.md:61-73` (§ Checkpoint) — `Open:` cites the consult file.
- `plugins/wh/skills/implementation/scripts/impl_env.sh:44` — create `consults/`.
- `plugins/wh/skills/implementation/REPORT.md:23` — new "Consultations" section next to Open items.
- `plugins/wh/skills/implementation/scripts/board.sh` — accept the `CONSULT` kind (or a new `consult.sh`).
- `tests/test_scripts.py` — test of the new script.
- `plugins/wh/.claude-plugin/plugin.json:3` — version bump; `docs/MANUAL.md` § 8 (known limits) updated.

## Code references
- `plugins/wh/skills/implementation/scripts/impl_env.sh:44-45` — `mkdir -p "$impl/qa" "$impl/retros" "$impl/progress" "$impl/acceptance"`; `consults/` joins it.
- `BOARD` `tests/test_scripts.py:18` — board test fixture to extend.

## Other references
- `docs/MANUAL.md` § 8: "a `SendMessage` to an agent that already finished resumes it with its context (that is how the enricher and the QA fixes work)" and "After a session restart, the enricher died with it" (`SKILL.md:55`).

## Open questions
- One file per consultation or a single append-only `CONSULTS.md`?
- Does the report keep every consultation or only those with impact beyond the item?
