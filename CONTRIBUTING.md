# Contributing to wh-harness

Thanks for taking the time to contribute. Improvements arrive through pull requests; bug reports and ideas arrive through [issues](https://github.com/Walter-Dalla/wh-harness/issues). By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Before you start

- **Bug or idea:** search the open issues first, then open one with the matching template.
- **Small fix** (typo, broken link, one-line bug): go straight to a pull request.
- **Anything larger:** open an issue first, so the approach is agreed before you write it.
- **Security problem:** do not open a public issue; see [SECURITY.md](SECURITY.md).

## Set up

Requirements: [Claude Code](https://claude.com/claude-code), `git`, `bash`, `python3` and [`shellcheck`](https://www.shellcheck.net/).

```bash
git clone https://github.com/<your-user>/wh-harness   # your fork
cd wh-harness

# use your local copy as the plugin
claude plugin marketplace add "$PWD"
claude plugin install wh@wh-harness
```

The plugin is cached: after each edit run `claude plugin update wh@wh-harness` and open a new session.

## Rules of the repository

- Everything is written in English: skills, templates, agents, scripts and docs.
- The skill has the procedure, the profile has the facts. No skill or agent cites a project command; it cites `profile § Section`.
- A change to a skill, an agent or the hook bumps `version` in [`plugins/wh/.claude-plugin/plugin.json`](plugins/wh/.claude-plugin/plugin.json) and updates [`docs/MANUAL.md`](docs/MANUAL.md).
- Scripts use `bash` and the Python standard library only, with no third-party dependency.
- New behavior comes with a test in `tests/`.
- No personal paths (`/home/<user>`, `C:\Users`) in `plugins/`, `examples/` or `tests/`; CI rejects them.

Where things live: [`docs/MANUAL.md`](docs/MANUAL.md) §1.

## Run the checks

These are the checks CI runs on every pull request:

```bash
python3 -m unittest discover -s tests
for f in plugins/wh/skills/*/scripts/*.sh; do bash -n "$f"; done
shellcheck -S warning plugins/wh/skills/*/scripts/*.sh
claude plugin validate ./plugins/wh --strict
claude plugin validate . --strict
```

## Open the pull request

1. Create a branch from `main`: `git checkout -b feat/short-description`.
2. Commit one logical change per commit, with a short imperative message prefixed by its type: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
3. Push to your fork and open the pull request against `main`. The template asks what changed and why, how you tested it, and which issue it closes (`Closes #123`).
4. Keep each pull request on one subject. CI must pass before review.

The maintainer reviews, may ask for changes, and merges. Your contribution is released under the project's [MIT license](LICENSE).
