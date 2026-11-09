# Common profile

## Clone
— (the current checkout, native Linux/WSL; worktrees under `.claude/worktrees/`) [owner]

## Toolchain
Python: `python3` (CI runs 3.11 and 3.13) [ci: ci.yml]. Shell: `bash`; `shellcheck` is not installed locally (CI runs it) [owner]. Plugin validation: `claude plugin validate ./plugins/wh --strict` [ci: ci.yml].

## Git
Main branch: `main`. PR remote: `origin` (GitHub `Walter-Dalla/wh-harness`) [git remote]. Merge to `main` goes through PRs [git log].

## Ports
— (no service) [owner]

## Navigation
`.codegraph/` at the root indexes the Python scripts (`plugins/wh/scripts/`, `plugins/wh/skills/*/scripts/`, `tests/`): `codegraph explore "<symbols or question>"`; `codegraph sync .` after editing [~/.claude/CLAUDE.md]. Skills, agents and docs are Markdown: `grep`/`Read` [owner].
Agent and integration worktrees have no `.codegraph/` (gitignored): query the clone's index with `codegraph explore -p <root> "…"` (Python files equal at the base) [retro: enricher, scripts]

## Docs
`CLAUDE.md` — map and rules (English only; skill = procedure, profile = facts; version bump on skill/hook change) [CLAUDE.md]
`docs/MANUAL.md` — full map, mechanisms, source formats, extending, known limits [CLAUDE.md]
`README.md` — short overview [CLAUDE.md]
`docs/pending/` — owner's open items, one file per item (`docs/pending/README.md` § Format) [docs/pending/README.md]
`docs/testes/` — test-drive reports [owner]

## Pending
`docs/pending/` [owner]

## Limits
No agent touches `~/.claude/` (user config, hooks), files outside the repo and the scratchpad, or the `examples/demo` fixtures beyond what a test needs [owner].
