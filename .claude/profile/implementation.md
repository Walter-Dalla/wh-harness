# Profile of /wh:implementation

## Build
— (no build; Python and shell run as they are) [owner]

## Tests
Area: `python3 -m unittest tests.<module>` (e.g. `tests.test_scripts`, `tests.test_refs`) [CLAUDE.md]
Suite: `python3 -m unittest discover -s tests -q` [CLAUDE.md]
Acceptance of an item = an area test that only goes green with the item done; for a Markdown-only item (skill, agent, doc), `python3 -m unittest tests.test_refs` (section references) plus a `grep` that shows the new text [owner].

## Checks
`for f in plugins/wh/skills/*/scripts/*.sh; do bash -n "$f"; done` (per item touching a `.sh`) [ci: ci.yml]
`shellcheck -S warning plugins/wh/skills/*/scripts/*.sh` (final QA, only where installed) [ci: ci.yml]
`python3 -m json.tool plugins/wh/.claude-plugin/plugin.json > /dev/null` (per item touching a manifest) [ci: ci.yml]
`claude plugin validate ./plugins/wh --strict` (final QA) [ci: ci.yml]
`! grep -rnIE --exclude-dir=__pycache__ '/home/[a-z]+|C:\\Users' plugins examples tests` (final QA: no personal paths) [ci: ci.yml]

## Disposable service
— [owner]

## Contract
Profile templates (`plugins/wh/skills/*/PROFILE.md`, `plugins/wh/skills/profile/COMMON.md`): a section rename breaks existing profiles and `check.py`. The `KEY=VALUE` fact sheet of `impl_env.sh` and the agent prompt fields (`Stage:`, `Mode:`…) are read by the skill and agents. Producer and consumer change in the same plan; `tests/test_refs.py` checks section references [owner].

## Union files
`docs/MANUAL.md` `plugins/wh/.claude-plugin/plugin.json` `tests/test_scripts.py` [owner]

## Protected files
`CLAUDE.md`, `README.md`, `.claude/profile/*.md`, `docs/reports/*`, `plugins/wh/.claude-plugin/plugin.json` (version) [owner]

## Enricher reading
Always: `CLAUDE.md`, `docs/MANUAL.md`, `plugins/wh/skills/implementation/SKILL.md` [CLAUDE.md]. When the task touches it: the skill's `PROFILE.md`, `LANES.md`, `ENVIRONMENT.md`, `TRIAGE.md`, `REPORT.md`, the agents in `plugins/wh/agents/` [owner].

## Visual or e2e QA
— [owner]

## Closing docs
Changelog: — . Version: `plugins/wh/.claude-plugin/plugin.json` `version` bump + `docs/MANUAL.md` [CLAUDE.md]. Open items: `docs/pending/` [docs/pending/README.md]. Feature map: — . Cleanup: — (no `cleanup.md`) [owner]

## Report
`docs/reports/<date>-<slug>.md` [owner]

## Models
— [owner]

## Worktree commands
Any Bash argument naming a path with `git` in it (e.g. `.gitignore`) is refused: read it with `Read` [retro: templates]
`board.sh` text with `<`, `>` or `->` is refused: write the text without them [retro: wiring]
No shell variables in paths (`W=…; sed $W/…`) and no `;`/`for` chains: one simple command per call [retro: wiring, qa-final]
`git reset --hard <hash>` is refused by the auto-mode classifier: check `git log --oneline -1` first and reset only when HEAD differs [retro: qa-final]
