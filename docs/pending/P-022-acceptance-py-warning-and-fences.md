---
id: P-022
status: open
created: 2026-11-10
related: []
---

# acceptance.py: no SyntaxWarning, and no item headings read inside code fences

## Problem
1. `plugins/wh/skills/implementation/scripts/acceptance.py:6` has `\`` in a normal docstring: every run prints `SyntaxWarning: "\`" is an invalid escape sequence` (Python 3.12+; a future SyntaxError). Reported by five lanes and the final QA of run wh-pendencias; `wave_prep.sh` has to drop stderr to keep it out of the wave attachment.
2. A `## ` line inside a fenced code block of a lane file is parsed as an item heading (enricher of run wh-pendencias caught it only by printing the parse).

## Strategy
1. Raw docstring (`r"""…"""`) at `acceptance.py:6`.
2. The lane-file parser skips lines inside ``` fences.
3. Tests in `tests/test_scripts.py`: running the script with `-W error` exits 0; a lane file with a fenced `## x · …` line yields only the real items.
4. Optional guard: CI compiles every script with `python3 -W error -m py_compile`.

## Locations
- `plugins/wh/skills/implementation/scripts/acceptance.py:6` — docstring
- `plugins/wh/skills/implementation/scripts/acceptance.py` (lane-file parsing) — fence skipping
- `tests/test_scripts.py` — the two tests
- `.github/workflows/ci.yml` — optional py_compile step

## Code references
- `acceptance.py` module docstring and its item parser [inferred]

## Other references
- Report `docs/reports/2026-11-10-wh-pendencias.md` (QA-final-05; retros phase1, check, inventory, wiring, agents-docs, enricher).

## Open questions
—
