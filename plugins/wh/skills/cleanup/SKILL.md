---
name: cleanup
description: Cleans up the .md files after a run: deletes executed plans, moves open items to their home, updates docs that cite changed code, removes the run's worktrees. Use at the end of /wh:implementation or for "clean up the docs".
---

# Cleanup of the `.md` files

Project profile (injected; `PROFILE_MISSING` = `Skill(wh:profile, "cleanup")` and then `Read` both files, because the injection below ran before the profile existed):
!`cat .claude/profile/_common.md .claude/profile/cleanup.md 2>/dev/null || echo PROFILE_MISSING`

Input: a `slug` from `/wh:implementation` (scope = `<main>...impl/<slug>` and the plan folder of profile § Consumed), or a list of plan files/folders and a commit range. You work on the run's branch; everything becomes one commit in the format of profile § Commit.

Every **open finding has a home**, and only one: the table in profile § Homes.

## 1. Inventory

- **Consumed:** the `.md` files the run read as instructions (profile § Consumed: plan and lanes, prompts, debts, prompt cited in the request). For each: executed in full, in part, or untouched (by the ids in the commits: `git log <main>..HEAD --format=%s`).
- **Affected:** `git diff <main>...HEAD --name-status` and the symbols, files, routes, constants and keys the diff created, renamed or deleted. Each old name and each deleted path, searched in the repo's `.md` files: `git grep -n -e '<name>' -- '*.md'`.

**Done when every consumed `.md` has a state and every changed name/path has the list of `.md` files that cite it.**

## 2. Save what is open

In each consumed `.md`, what was **not** executed or remained as a finding (skipped item, partial, `HUMAN`, decision for later, "out of scope") goes to its home from profile § Homes, with the evidence in one line, if the home does not have it yet. A status or open-item line the run resolved (check in the code) leaves.

**Done when every open item of the consumed files is in a home and no home lists something this run already resolved.**

## 3. Delete the executed

- Executed in full: `git rm` (or `rm -r` outside git, like the plan folder once the report exists). In part: only the done items leave; the file keeps the rest.
- An empty folder leaves; an index that pointed at the file (README, `CLAUDE.md`, "on demand") loses the line.
- Pruning of the changelog and of the task reports by the rule of profile § Pruning.
- Always stays: the list of profile § Permanent.

**Done when no fully executed `.md` exists and no done item remains in a partial `.md`.**

## 4. Update what changed

For each affected `.md` from step 1: old name replaced by the new, the deleted one removed, the rule the diff changed adjusted by checking the code (`_common § Navigation`), never from the report. Feature map through the skill of profile § Homes. A code comment that cites a deleted `.md`: point at the commit (`git show <hash>:<file>`).

**Done when `git grep` of each old name and each deleted path finds nothing outside the changelog, the report and the history.**

## 5. Commit

`git add -A` of the touched `.md` files; commit in the format of profile § Commit, with the list of deleted files and of moved findings (home → item) in the body.

## 6. Worktrees

Only the worktrees **of the run** (`git worktree list --porcelain`): with `slug`, those on branch `impl/<slug>-*` and the agent ones (`worktree-agent-*`) whose HEAD is a commit of `<main>..impl/<slug>` (the `worktree-agent-*` branch goes with it: `git branch -D`); without it, those whose branch is already merged into `HEAD` (`git branch --merged HEAD`). Any other (owner, another session) stays as is and is listed in the answer. For each one:

- **Uncommitted change** (`git -C <wt> status --porcelain` with output): `git -C <wt> add -A`. Content already saved when `git -C <wt> diff --cached --quiet <ref> -- <files from status>` passes against `<main>` or `origin/<branch>`; then the worktree goes straight to removal. Otherwise, commit on the worktree's branch in the format of profile § Commit (detached HEAD: `git -C <wt> switch -c wt/<folder>` first).
- **Removal:** `git worktree remove <wt>`; `--force` only for a change already saved in `<main>` or `origin/<branch>`; locked, `git worktree unlock <wt>` first. The `impl/…` branch stays. At the end, `git worktree prune`.

**Done when no worktree of the run remains in `git worktree list`, and every change of the removed ones is in a commit, in `<main>` or in `origin/<branch>`.**

Answer (≤ 8 lines): deleted, partial, moved findings, updated `.md` files, removed worktrees (branch and new commit, if any).
