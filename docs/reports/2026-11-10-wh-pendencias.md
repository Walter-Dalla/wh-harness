# wh pending items P-005 to P-020: scripts, profile Commands block, check.py and agent rules · 2026-11-10 · impl/wh-pendencias · PR on GitHub
Request: implement the owner's 5-point list (split into P-008…P-020) and the open P-005…P-007, each validated against main 0.8.0, dropping what is covered, obsolete or badly formulated. Delivered: three phase-1 script fixes, a parseable `## Commands` profile block validated by `check.py`, six new scripts that take deterministic turns off the orchestrator and QA, two `check.py` checks, three agent/skill rules; version 0.9.0. 23 plan items, 23 green.
Lanes: W1 `phase1` (items 1–4), `check` (5–7), `inventory` (8–10); W2 `runners` (11–13), `wiring` (14–18), `agents-docs` (19–21); orchestrator 22–23. All DONE.

## Errors
No remaining failure: suite 120 tests OK, shellcheck clean, `claude plugin validate --strict` passed, personal-path grep clean, 23/23 Acceptances green at the tip (final QA and retest).
No merge conflict (six `--no-ff` merges, `git show --cc` empty).
Fixes made at integration by the orchestrator: QA-runners-04 `5f84fba` (ENVIRONMENT.md health passes `--slug`), QA-final-01 `e076dd9` (report skeleton `--out <intwt>/…`), QA-final-03 `498d47d` (new_names.py: `+=`/`|=` is not a typed declaration; regression line in `test_only_declared_names`, red before the fix).
Deviation from the plan, accepted: item 2's lock is a noclobber lock file, not `mkdir` (uutils coreutils 0.8.0 `mkdir` raced: duplicates with mkdir, 01–08 with noclobber).

## Open items
- P-015 (SubagentStart hook) **dropped**: on Claude Code 2.1.322 its input is `agent_id` + `agent_type` only, no prompt for `prompt_graph.py --query`; recorded in MANUAL § 8. Replacement direction → P-021 (PreToolUse on `Agent`).
- P-016 reduced to two sentences (SKILL.md § 1 wrong-branch case, COMMON.md § Git): switching the clone was already forbidden. P-020 reduced to one MANUAL sentence: the `fable` alias already resolves to `claude-fable-5-2` (enricher of this run, dispatched with `model: "fable"`); no pin, `Plan.md` template and marker untouched.
- `acceptance.py:6` SyntaxWarning and `## ` headings read inside code fences → P-022.
- new_names.py limits (fields/methods with no `=` or keyword, triple quote inside a one-line string, trailing kwarg, unpacking, `Map<K,V>=`) → P-023. Gate 3 of `impl-qa.md` states them; the list is input, never a verdict.
- Contracts changed: the implementation profile template starts with `## Commands` (every existing profile is `MISSING` in `check.py` until `/wh:profile implementation`; this repo's is done, item 22); `impl_env.sh --pull-only` and the new phase-1 order; `scope.sh --classify`; the enricher's `WAVE … Attachment:` message. Until 0.9.0 is installed, agents launched from the installed plugin read the old texts.
- Decisions taken without the owner: none (P-010 and P-018 answered by the owner). Unconfirmed `[inferred]` profile lines: none.

## Consultations
— (no consultation; the two WAVE consults and the plan questions are in PLAN.md § Decisions)

## QA
Decisions contested: QA-inventory-01: the code QA judged the 503-name noise of `new_names.py` "acceptable documented risk"; the orchestrator overrode it (measured risk = bug): comment/docstring skip (503 → 496), then "declared names only" (→ 142), retested fixed. QA-wiring-01 (drop `impl-dev` from the `profile_run.sh` row): declined, impl-dev reaches it through ENVIRONMENT § Tests and checks; QA-final-04 is the same point (below).
Fixed and retested: QA-inventory-01 `db3f6fd` `2116a48`, -02 `2b8f9a0`, -03 `221c755` (retest clean); QA-runners-01 `a6d11be` (wave_prep.sh fails on a crashed acceptance.py instead of `WAVE CLEAN`), -02 `7730a74`, -03 `d169193`, -04 `5f84fba` (retest clean); QA-final-01 `e076dd9`, -03 `498d47d` (retest clean). Fixed, checked by Acceptance (low): QA-check-02 `3068c3c`, QA-wiring-02 `db28348`.
Recorded, no code: QA-check-01 (bare name of an untracked file reported absent; by spec), QA-phase1-01 (NN 100 after 99), QA-phase1-02 (SIGKILLed ask leaves the lock; designed message), QA-inventory-04/05 (→ P-023), QA-final-02 (`check.py` keeps the first well-formed § Commands key, `profile_run.sh` the first line: a malformed line before a good one passes the check and fails at run time), QA-final-04 (`impl-dev.md:44` does not name `profile_run.sh`), QA-final-05 (→ P-022).
Deeper review: `/code-review ultra <PR number>`, command in the final answer.

## Problems found
- `plugins/wh/skills/implementation/SKILL.md:27` still says the board is appended through `printf … >>`; every board line goes through `board.sh` (wiring).
- `acceptance.py:6` SyntaxWarning on every run (five lanes and the final QA) → P-022.
- `check.py` reports `context.json` and `settings.json` MISSING in this repo, and before this run also the two project agents: unchanged by this run, pre-existing on main.

## Consolidated retro
| # | Severity | Category | Evidence (lanes) | Proposal | Who applies |
|---|---|---|---|---|---|
| 1 | high | Code standard | enricher, orchestrator, inventory: `new_names.py` was dictated without running the rule on a real diff (503 names); the code QA then accepted it by spec match; the orchestrator redefined it twice | `impl-enrich.md` § Certainty: a dictated heuristic is prototyped on a real diff with its output size in the analysis; `impl-qa.md` gate 4: a script whose output feeds a judgment is run on the lane's range and an unusable measured output is a bug | repo |
| 2 | high | Automatic check | enricher, phase1: the `mkdir` lock was dictated as atomic without testing the fix; uutils `mkdir` raced | `impl-enrich.md` risk list, concurrency: a dictated lock is exercised under the parallel load that showed the bug; `LANES.md`/TRIAGE: script locks use bash noclobber | repo |
| 3 | medium | Steering doc | enricher, orchestrator: `Write` refused `ANALYSIS.md` and a code-QA output in the clone, contradicting `ENVIRONMENT.md` § Files outside the worktree | `ENVIRONMENT.md` § Files outside the worktree and `SKILL.md` § 2 step 1: the answer-under-its-path fallback applies in the clone too | repo |
| 4 | medium | Code standard | enricher, qa-final: `report_skeleton.py --out` relative path resolved against the clone (QA-final-01) | `impl-enrich.md` risk list, CLI line: for each path argument, what a relative value resolves against, with a test | repo |
| 5 | medium | Automatic check | phase1, check, inventory, wiring, agents-docs, runners, qa-final, enricher, orchestrator: `acceptance.py` SyntaxWarning on every run; `## ` inside a fence parsed as an item | → P-022; CI `python3 -W error -m py_compile` on every script | repo |
| 6 | medium | Information access | orchestrator: the request file was in another session's scratchpad; found by a filesystem-wide `find` (120 s timeout) | intake: a path argument outside the repo is read as the request file | repo |
| 7 | medium | Worktree commands | check: `board.sh` text with backticks or `|` refused | profile § Worktree commands line extended — **applied** | repo |
| 8 | low | Worktree commands | runners, wiring, inventory, qa-final: `unittest discover -s <abs path>` fails "Start directory is not importable" | profile § Worktree commands: suite from the worktree root or `profile_run.sh suite` — **applied** | repo |
| 9 | low | Tool economy | enricher: Claude Code runtime facts proven by grepping a 340 MB binary (timeout, ~40 excerpts in context) | `impl-enrich.md` § Certainty: a runtime fact is an owner question or `[undetermined]` with a verification step | repo |
| 10 | low | Steering doc | orchestrator: a finding in a file another lane had already merged (QA-runners-04) has no rule; decisions appended at the end of PLAN.md | `LANES.md` §3 step 3: orchestrator fix in `<intwt>`, commit `QA-<lane>-NN`; `SKILL.md` § 2: decisions go in PLAN.md § Decisions | repo |
| 11 | low | Tests | runners: subclassing or importing `ScriptsTest` reruns it in every new module | profile § Tests: borrow helpers as `import tests.test_scripts as ts`, never import the TestCase | repo |
| 12 | low | Skill | qa-final, wiring, agents-docs: the seam verification rode in `Verify:` free-form; stale `SKILL.md:27`; a list gaining an entry from a new folder needs the folder sentence too | `SKILL.md` phase 5: a `Seams:` line; fix SKILL.md:27; enricher names the folder sentence | repo |
