---
id: P-003
status: open
created: 2026-11-09
related: [P-001, P-002]
---

# Two entry modes for the orchestrator: raw request or pending file

## Problem
`/wh:implementation` has a single entry: a free-text request passed verbatim to the enricher. The owner wants two:
- **Raw request** (unstructured): the orchestrator sends it to the structurer ([P-002](P-002-structurer-agent.md)), which writes the pending file(s), and those go to the `fable` enricher.
- **Pending file** (already structured): the orchestrator receives the file (or its id) and sends it straight to the enricher, skipping the structurer.

## Strategy
1. Phase 1 decides the mode from the arguments: a path or id that resolves in the pending folder (`_common § Pending`) = file mode; anything else = raw mode. A script does the detection (deterministic), printing `INTAKE=file|raw` and `PENDING=<paths>` next to the other `KEY=VALUE` lines of `impl_env.sh`.
2. Raw mode: phase 2 step 0 dispatches the structurer, then the enricher's analyze prompt carries `Pending: <paths>` instead of `Request:` (the raw request still goes along, as context).
3. File mode: the analyze prompt carries `Pending: <paths>` directly.
4. Several pending files in one call: one run, one plan; the enricher decides lanes as today.
5. The slug comes from the pending file's title in file mode.

## Locations
- `plugins/wh/skills/implementation/SKILL.md:12-18` (phase list) — mention the two intakes.
- `plugins/wh/skills/implementation/SKILL.md:34-43` (§ 1 Environment) — detect the mode, slug from the file.
- `plugins/wh/skills/implementation/SKILL.md:49` (§ 2, step 1, analyze prompt) — `Pending:` field.
- `plugins/wh/skills/implementation/scripts/impl_env.sh:44-45, 79` — create the folders and print the new keys.
- `plugins/wh/agents/impl-enrich.md:17` (Stage `analyze`) — the prompt now gives `Pending:`; read it before the request.
- `tests/test_scripts.py` — cases for both modes of the detection.
- `docs/MANUAL.md` § 4 and § 6 — usage and headless mode with a pending file.

## Code references
- `plugins/wh/skills/implementation/scripts/impl_env.sh:79` — `echo "BOARD=…"`: the fact-sheet output the new keys join.
- `BOARD` `tests/test_scripts.py:18` — existing script test fixture to extend.

## Other references
- [P-001](P-001-pending-file-intake.md) — the file format.
- Visual flow of the current system: https://claude.ai/artifact/XNngkicGyKkWhEXV4UeQGi

## Open questions
- Syntax for file mode: `/wh:implementation P-001`, `/wh:implementation docs/pending/P-001-….md`, or a flag?
- When the raw request names an existing pending item, merge into it or create a new one?
