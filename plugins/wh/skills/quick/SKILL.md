---
name: quick
description: Light route for a small change (a label, a visible text, a style value, a one-line fix): one edit, one check, one commit and the PR, with no enricher, QA agent, retro or report. A size gate sends anything larger to /wh:implementation.
argument-hint: <the change, in one sentence>
disable-model-invocation: true
model: sonnet
effort: low
---

# Quick

Project profile (injected; `PROFILE_MISSING` = go on with the defaults below, this skill never writes a profile):
!`cat .claude/profile/_common.md .claude/profile/implementation.md 2>/dev/null || echo PROFILE_MISSING`

Request: $ARGUMENTS

You make this one change yourself, in this turn, and stop at the open PR. No subagent, no plan file, no retro, no report, no question to the owner unless the request names two different things. The whole run is about eight tool calls: if you are past fifteen, the task is not quick (§ Escalate).

Script: `${CLAUDE_PLUGIN_ROOT}/skills/quick/scripts/quick.sh` (below, `quick.sh`). Main branch and remote: `_common § Git` (no profile: `main`, `origin`).

## 1. Start

`quick.sh start <slug> --main <main> --remote <remote>` at the repository root (slug: two or three words, kebab-case). It creates the worktree `WT` on the branch `quick/<slug>`, born from the remote main; the clone's checkout is never touched, so its branch and local changes do not matter. Every edit and command below happens in `WT`. `QUICK FAILED` = stop and say the reason. `PROFILE=missing` in its output (the remote main has no implementation profile, even if the clone does): the gate cannot see the contract paths, so in step 2 you compare the files to change with the Contract section injected above yourself.

## 2. Locate

One search, in `WT`: the text or name the request cites, with `git -C <WT> grep -n -F '<old text>'` (it also shows the tests, translations and snapshots that repeat it), or `_common § Navigation` when the request names a symbol. A `[wh:prompt-graph]` block that came with the request already points at the files: start there.

Stop here and escalate, before editing, when the search shows any of: more than 3 files to change, a path of profile § Contract, a behavior to decide (what happens when, which rule), or a text whose rule lives elsewhere (legal or store text, a value a test computes).

## 3. Edit

The minimum the request asks, in the pattern of the neighboring lines; every repetition of the changed text that step 2 found (test, translation, snapshot) in the same edit. The rules of `CLAUDE.md`/`AGENTS.md` hold. A neighboring problem goes in the final answer, not in the diff.

## 4. Check

- `${CLAUDE_PLUGIN_ROOT}/skills/implementation/scripts/profile_run.sh typecheck <WT>`, then the area test of profile § Tests for the touched file; no area test fits = `profile_run.sh suite <WT>`. The verdict is the exit code. `PROFILE_RUN FAILED` or no profile: the test command the `README` or the CI workflow shows.
- `quick.sh gate <WT> --main <main> --remote <remote>`: `QUICK OK` = go on; `QUICK ESCALATE: <reasons>` = § Escalate.

A red check you cannot fix by correcting your own edit = § Escalate. Never weaken a test to pass. A check that cannot even start in the fresh worktree (missing dependency or build output, not your edit): run the setup `_common § Toolchain` names, once; still not running = do not finish: keep `WT`, and tell the owner what is missing and the path.

## 5. Commit and finish

`git -C <WT> add -A` and `git -C <WT> commit -m 'quick: <what changed, one line>'` with the session's co-authorship line; then `quick.sh finish <WT> --main <main> --remote <remote> --body '<one line: what changed and how it was checked, plus the session's PR footer>'` (the text single-quoted, each `'` in it as `'\''`). It runs the gate again, pushes, opens the PR (`PR=<url>`) or prints the merge command (`PR=none`, `MERGE=…`), and removes the worktree. `QUICK FAILED: gh pr create failed` = the branch is on the remote and the worktree is kept: give the owner the branch and the error.

Answer (≤ 4 lines): the PR link or the merge command, the file and line changed, the check that ran with its exit, anything you noticed and left alone.

## Escalate

The change is not quick. Do not push. Say in one line why (the gate's reasons, or what step 2 showed) and give the owner the command `/wh:implementation <the request>`; then `quick.sh drop <WT>` unless the edit is worth keeping for them to look at (say the path). Never raise `--max-files` or `--max-lines` to get through: the limits are the definition of quick.
