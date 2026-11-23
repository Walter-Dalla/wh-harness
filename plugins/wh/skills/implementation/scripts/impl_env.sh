#!/usr/bin/env bash
# Phase 1 of /wh:implementation, deterministic: checks the clone, prepares the task folders and the integration
# worktree, and prints the facts every later prompt needs, one `KEY=VALUE` per line.
#
#   impl_env.sh <slug> [--main <branch>] [--remote <name>] [--no-pull] | --pull-only [--main <branch>] [--remote <name>]
#
# Run at the clone root, on the main branch, clean. Exit 1 with `ENV FAILED: <reason>` when the session cannot
# go on (not the root, wrong branch, local changes, remote unreachable, a stale impl/<slug>); nothing is changed
# before the checks pass. <main> is the base branch of the run: the repo's main, or another branch the owner names
# as the base (stacked work), which must be the clone's checkout and exist on the remote.
# Idempotent: an existing integration worktree on impl/<slug> is reused (REUSED=worktree). A branch impl/<slug>
# that already exists is compared with <main>: nothing ahead of it = the leftover of a run that landed, brought to
# <main> (REUSED=fast-forwarded); ahead and not behind, with no worktree = a run to resume (REUSED=branch); ahead
# and behind with no worktree = `ENV FAILED` (the owner says which). AHEAD= and BEHIND= are the counts against
# <main> after that. The same facts are written to .impl/<slug>/env, which lane_prompt.sh reads.
# --pull-only: the same checks and `git pull --ff-only`, then ROOT=, MAIN=, REMOTE=, BASE= and `PULL OK`; nothing
# else is changed (no exclude line, no .impl/, no worktree, no gh, no codegraph).
set -u

fail() { echo "ENV FAILED: $*"; exit 1; }

[ $# -ge 1 ] || fail "usage: impl_env.sh <slug> [--main <branch>] [--remote <name>] [--no-pull] | --pull-only [--main <branch>] [--remote <name>]"
pull_only=0
if [ "$1" = --pull-only ]; then pull_only=1; slug=; else slug=$1; fi
shift
main=main; remote=origin; pull=1
while [ $# -gt 0 ]; do
  case $1 in
    --main) main=${2:?--main without a value}; shift 2 ;;
    --remote) remote=${2:?--remote without a value}; shift 2 ;;
    --no-pull) pull=0; shift ;;
    *) fail "unknown option $1" ;;
  esac
done
if [ "$pull_only" = 1 ]; then
  [ "$pull" = 1 ] || fail "--pull-only with --no-pull"
else
  case $slug in *[!a-z0-9-]*|'') fail "slug '$slug' is not kebab-case" ;; esac
fi

root=$(git rev-parse --show-toplevel 2>/dev/null) || fail "not inside a git repository"
[ "$root" = "$(pwd -P)" ] || fail "run at the repository root ($root), not in $(pwd -P)"
branch=$(git branch --show-current)
[ -n "$branch" ] || fail "clone is on a detached HEAD, not $main"
[ "$branch" = "$main" ] || fail "clone is on '$branch', not $main (never switch it; if the owner names '$branch' as the base of this run, pass --main $branch to every impl_env.sh call)"
[ -z "$(git status --porcelain)" ] || fail "clone has local changes (git status)"
git ls-remote --exit-code --heads "$remote" "$main" >/dev/null 2>&1
case $? in
  0) ;;
  2) fail "$main is not on $remote (the base branch has to be there: git push -u $remote $main)" ;;
  *) fail "$remote/$main does not answer (gh auth setup-git?)" ;;
esac
if [ "$pull" = 1 ]; then
  git pull --ff-only --quiet "$remote" "$main" || fail "git pull --ff-only failed"
fi

if [ "$pull_only" = 1 ]; then
  echo "ROOT=$root"
  echo "MAIN=$main"
  echo "REMOTE=$remote"
  echo "BASE=$(git rev-parse "$main")"
  echo "PULL OK"
  exit 0
fi

# What to do with the integration branch, decided before anything is written (the failures stop here).
intwt=$root/.claude/worktrees/impl-$slug
ahead=0; behind=0; reused=no; plan=create
count() {
  ahead=$(git rev-list --count "$main..impl/$slug" 2>/dev/null) || fail "cannot compare impl/$slug with $main"
  behind=$(git rev-list --count "impl/$slug..$main" 2>/dev/null) || fail "cannot compare impl/$slug with $main"
}
if [ -d "$intwt" ]; then
  cur=$(git -C "$intwt" branch --show-current 2>/dev/null)
  [ "$cur" = "impl/$slug" ] || fail "$intwt exists on '$cur', not impl/$slug (remove it or pick another slug)"
  count; reused=worktree; plan=keep
  if [ "$ahead" = 0 ] && [ "$behind" != 0 ]; then
    [ -z "$(git -C "$intwt" status --porcelain)" ] || fail "$intwt is $behind commit(s) behind $main and has local changes (the leftover of an earlier run: commit or remove it, or pick another slug)"
    reused=fast-forwarded; plan=forward-worktree
  fi
elif git show-ref --verify --quiet "refs/heads/impl/$slug"; then
  count; reused=branch; plan=add
  if [ "$ahead" = 0 ] && [ "$behind" != 0 ]; then
    reused=fast-forwarded; plan=forward-branch
  elif [ "$ahead" != 0 ] && [ "$behind" != 0 ]; then
    fail "impl/$slug already exists, $ahead commit(s) ahead of $main and $behind behind, with no worktree: the leftover of an earlier run (already landed: git branch -D impl/$slug, or pick another slug) or a run to resume (git worktree add $intwt impl/$slug, then this command again)"
  fi
fi

exclude=.git/info/exclude
touch "$exclude"
for line in .impl/ .claude/worktrees/; do
  grep -qxF "$line" "$exclude" || printf '%s\n' "$line" >> "$exclude"
done

impl=.impl/$slug
mkdir -p "$impl/qa" "$impl/retros" "$impl/progress" "$impl/acceptance" "$impl/agent_chat"
[ -f "$impl/BOARD.md" ] || : > "$impl/BOARD.md"

pr_mode=none
if command -v gh >/dev/null 2>&1 && gh repo view --json nameWithOwner >/dev/null 2>&1; then pr_mode=github; fi

codegraph=absent
if [ -d .codegraph ]; then
  codegraph=present
  if command -v codegraph >/dev/null 2>&1; then codegraph sync . >/dev/null 2>&1 && codegraph=synced; fi
fi

profile=ok
for f in .claude/profile/_common.md .claude/profile/implementation.md; do [ -f "$f" ] || profile=missing; done

case $plan in
  create) git worktree add --quiet -b "impl/$slug" "$intwt" "$main" || fail "git worktree add -b impl/$slug failed" ;;
  forward-worktree) git -C "$intwt" merge --ff-only --quiet "$main" || fail "cannot fast-forward $intwt to $main" ;;
  forward-branch) git branch -f "impl/$slug" "$main" >/dev/null || fail "cannot move impl/$slug to $main" ;;
esac
case $plan in
  add|forward-branch) git worktree add --quiet "$intwt" "impl/$slug" || fail "git worktree add of the existing impl/$slug failed" ;;
esac
[ "$reused" = no ] || count

facts() {
  echo "ROOT=$root"
  echo "SLUG=$slug"
  echo "MAIN=$main"
  echo "REMOTE=$remote"
  echo "BASE=$(git rev-parse "$main")"
  echo "REUSED=$reused"
  echo "AHEAD=$ahead"
  echo "BEHIND=$behind"
  echo "GIT=$(command -v git)"
  echo "PR_MODE=$pr_mode"
  echo "PROFILE=$profile"
  echo "CODEGRAPH=$codegraph"
  echo "IMPL=$root/$impl"
  echo "BOARD=$root/$impl/BOARD.md"
  echo "INTWT=$intwt"
}
facts > "$impl/env" || fail "cannot write $impl/env"
cat "$impl/env"
echo "ENV OK"
