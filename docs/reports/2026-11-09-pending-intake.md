# Pending intake, structurer and agent chat · 2026-11-09 · impl/pending-intake · PR on GitHub
Implements docs/pending P-001..P-004 (wh 0.7.2 → 0.8.0): `/wh:implementation` gains two intakes — a raw request goes through the new `impl-structure` agent, which writes one pending file per item (asking the owner first when needed); pending ids/paths, or no argument (= every `status: open` file), go straight to the enricher. `intake.sh` decides the mode, slug and next id; `_common § Pending` (default `docs/pending/`, format `PENDING.md`) is the home of open items at close; every enricher consultation is persisted in `.impl/<slug>/agent_chat/NN-<lane>-<item>.md` through `agent_chat.sh` and listed in the report. `.impl/` joins this repo's `.gitignore`.
Lanes: scripts (items 1–4, 4 commits), templates (5–7, 3 + 1 QA fix), wiring (8–13, 6 + 2 QA fixes); orchestrator: item 14 (2 commits), profile (2), final-QA fixes (3), pending files P-005..P-007, report.

## Errors
None remaining: suite 63 OK (`python3 -m unittest discover -s tests -q`); `acceptance.py PLAN.md` 14 green; `claude plugin validate ./plugins/wh --strict` passed; personal-path grep clean. `shellcheck` not run locally (not installed): CI is the first run. No merge conflict.

## Open items
- Pending ids reused once landed files leave the folder: `intake.sh --next` printed `P-001` after this run removed P-001..P-004; the new files were numbered from P-005 by hand → P-005
- `agent_chat.sh` NN collision between parallel lanes (QA-scripts-01, low) → P-006
- `intake.sh` reads the pending folder before `impl_env.sh` pulls (QA-wiring-05, low) → P-007
- `## Pending` of this repo's `_common.md` landed in the orchestrator's close commit 5888c33, not in a separate owner commit as PLAN item 14 said (QA-final-07, product judgment): review the line in the PR.
- Profile sections `—`: Build, Ports, Disposable service, Visual or e2e QA (phases skipped: no build, no service, no visual QA).
- Owner decision kept as is: `/wh:adopt` § 5 still tells other repos to put `.impl/` in `.git/info/exclude`, not `.gitignore`; only this repo ignores it.

## Consultations
None: no lane sent a `QUESTION` during the run (`agent_chat/` empty).

## QA
- templates (code): QA-templates-01 risk low, confirmed at integration (`intake.sh` from lane scripts); QA-templates-02 standard low → fixed f811288.
- scripts (code): QA-scripts-01 → P-006; QA-scripts-02 (unanchored `status: open`) recorded, then reproduced in the final QA → fixed 06799fa.
- wiring (code): QA-wiring-01/02 (report cites ids before they exist; landed id reuse within a run) → fixed 8680f46; QA-wiring-03 (free text in shell arguments) → fixed 4ccafdf; retested, no new finding. QA-wiring-04 (version) fixed by 5888c33; QA-wiring-05 → P-007.
- final: QA-final-01 (`Merge into:` clone paths), 02 (`next` from `<root>` in cleanup/PENDING.md) medium; 03 (`status: opened`), 04 (`next` word typed by the owner; ids with punctuation) low bugs; 05, 06 standards → fixed 06799fa, 670e743 (`intake.sh <root> next` became `--next`); 07 → Open items. Retest at 670e743: 01–06 fixed, no critical/high; new QA-final-08 (low bug: only one trailing punctuation mark stripped, `P-001.,` read as raw) → fixed c9c086e, checked by the suite and a hand run.
- Deeper review, optional: `/code-review ultra <PR number>` (command in the final answer).

## Problems found
- `plugins/wh/skills/implementation/scripts/acceptance.py:6`: `SyntaxWarning` (invalid escape in the docstring) on every run (reported by 4 agents).
- `plugins/wh/skills/implementation/SKILL.md:27`: "The board: appended through `printf … >>`" is stale (`board.sh` writes the board).
- `impl_env.sh` refuses a clone whose only change is the run's own untracked pending files; the orchestrator moved `docs/pending/` aside and re-committed it in the integration worktree.
- `check.py links` warns on bare file names in profiles (`ENVIRONMENT.md`, `impl_env.sh`) that are not paths.
- The three copies of the pending Format block (`PENDING.md`, `docs/pending/README.md`, MANUAL § 5.4) have no test tying them.

## Consolidated retro
| # | Severity | Category | Evidence (lanes) | Proposal | Who applies |
|---|---|---|---|---|---|
| 1 | high | Automatic check | orchestrator: `impl_env.sh` refused the clone dirtied by the run's own `docs/pending/` | `impl_env.sh`: accept untracked files of the pending folder and commit them first in `<intwt>` | repo |
| 2 | medium | Automatic check | scripts, templates, wiring, orchestrator: `acceptance.py:6` SyntaxWarning | raw docstring (`r"""`) | repo |
| 3 | medium | Code standard | orchestrator, qa-final: 2 medium seam bugs visible only across lanes | `LANES.md` §3 step 8: cheap static QA of the wave's merged diff on cross-lane citations; SKILL § 5 keeps a "seams to check" note | repo |
| 4 | medium | Tool economy | scripts: 4+ git calls per item (add, commit, push, log) | `scripts/commit_item.sh <worktree> <remote> <branch> <id> <msg> <files…>` | repo |
| 5 | medium | Steering doc | orchestrator, enricher: owner answered "explain me more" twice; folder renamed after the plan (`consults/` → `agent_chat/`) | `SKILL.md` § 2 / `impl-enrich.md`: each question says in one line what the mechanism is; new shared names go to QUESTIONS | repo |
| 6 | low | Worktree guard | templates, wiring, qa-final: refusals on `.gitignore`, `<`/`>`/`->`, shell variables, `git reset --hard` | applied: profile § Worktree commands (4 lines); `ENVIRONMENT.md` § Bash in the agent worktree could carry the generic ones | applied (profile) / repo |
| 7 | low | Navigation | enricher, scripts: worktrees have no `.codegraph/` | applied: `_common § Navigation` line; `impl-dev.md` start step 3 to say "if the clone has `.codegraph/`" | applied (profile) / repo |
| 8 | low | Steering doc | scripts, templates, wiring: lane specs with a union line edit undeclared, a contradictory `next` output, a line cap that did not fit | `LANES.md` §1: one output contract per command; caps as targets; union edits in `May touch` | repo |
| 9 | low | Automatic check | orchestrator: `shellcheck` absent locally | `_common § Toolchain` install hint; `preflight.sh` warns | owner |
