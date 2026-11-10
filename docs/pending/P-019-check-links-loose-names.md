---
id: P-019
status: open
created: 2026-11-10
related: []
---

# check.py link WARNs for loose file names in CLAUDE.md

## Problem
Owner: "check.py dá WARN links para CLAUDE.md → PROFILE.md, check.py, preflight.sh, scope.sh (nomes soltos). Corrigir citando caminhos completos ou fazendo o check.py resolver nomes soltos de forma sensata."
Confirmed on main: `check.py` prints `WARN links … CLAUDE.md → PROFILE.md; CLAUDE.md → check.py; CLAUDE.md → preflight.sh; CLAUDE.md → scope.sh`. The same WARN also lists loose names of `.claude/profile/implementation.md` (`ENVIRONMENT.md`, `LANES.md`, `PROFILE.md`, `REPORT.md`, `TRIAGE.md`, `board.sh`, `check.py`, `cleanup.md`, `impl_env.sh`) and of `_common.md` (`Walter-Dalla/wh-harness`, `~/.claude/`) — not cited by the owner.

## Strategy
1. Before implementing: validate against the current main (0.8.0); drop with justification in the report if not.
2. Either cite full paths in `CLAUDE.md`, or make `check.py` resolve loose names sensibly.

## Locations
- `CLAUDE.md:6` — `PROFILE.md` loose [code CLAUDE.md:6]
- `CLAUDE.md:9` — `scope.sh`, `preflight.sh`, `check.py` loose (protected file: owner reviews) [code CLAUDE.md:9]
- `plugins/wh/skills/adopt/scripts/check.py:192` (`Check.links`) — token filter and `os.path.exists(self.p(tok))` [code plugins/wh/skills/adopt/scripts/check.py:192]
- `tests/test_adopt.py` / `tests/test_scripts.py` — links test [inferred]

## Code references
- `Check.links` `plugins/wh/skills/adopt/scripts/check.py:192` — cited-path check; a token without `/` but with a known extension is checked at the root [code plugins/wh/skills/adopt/scripts/check.py:200]

## Other references
- `docs/MANUAL.md` § 6 Validation.

## Open questions
- If check.py resolves loose names: unique basename match in the repo (`git ls-files`) = OK, ambiguous or none = WARN?
