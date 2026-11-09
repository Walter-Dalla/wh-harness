#!/usr/bin/env bash
# Phase 1 of /wh:implementation, deterministic: checks the clone, prepares the task folders and the integration
# worktree, and prints the facts every later prompt needs, one `KEY=VALUE` per line.
#
#   impl_env.sh <slug> [--main <branch>] [--remote <name>] [--no-pull]
#
# Run at the clone root, on the main branch, clean. Exit 1 with `ENV FAILED: <reason>` when the session cannot
# go on (not the root, wrong branch, local changes, remote unreachable); nothing is changed before the checks pass.
# Idempotent: an existing integration worktree on impl/<slug> is reused.
set -u

fail() { echo "ENV FAILED: $*"; exit 1; }

[ $# -ge 1 ] || fail "usage: impl_env.sh <slug> [--main <branch>] [--remote <name>] [--no-pull]"
slug=$1; shift
main=main; remote=origin; pull=1
while [ $# -gt 0 ]; do
  case $1 in
    --main) main=${2:?--main without a value}; shift 2 ;;
    --remote) remote=${2:?--remote without a value}; shift 2 ;;
    --no-pull) pull=0; shift ;;
    *) fail "unknown option $1" ;;
  esac
done
case $slug in *[!a-z0-9-]*|'') fail "slug '$slug' is not kebab-case" ;; esac

root=$(git rev-parse --show-toplevel 2>/dev/null) || fail "not inside a git repository"
[ "$root" = "$(pwd -P)" ] || fail "run at the repository root ($root), not in $(pwd -P)"
branch=$(git branch --show-current)
[ "$branch" = "$main" ] || fail "clone is on '$branch', not $main"
[ -z "$(git status --porcelain)" ] || fail "clone has local changes (git status)"
git ls-remote --exit-code --heads "$remote" "$main" >/dev/null 2>&1 || fail "$remote/$main does not answer (gh auth setup-git?)"
if [ "$pull" = 1 ]; then
  git pull --ff-only --quiet "$remote" "$main" || fail "git pull --ff-only failed"
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

intwt=$root/.claude/worktrees/impl-$slug
if [ -d "$intwt" ]; then
  cur=$(git -C "$intwt" branch --show-current 2>/dev/null)
  [ "$cur" = "impl/$slug" ] || fail "$intwt exists on '$cur', not impl/$slug (remove it or pick another slug)"
elif git show-ref --verify --quiet "refs/heads/impl/$slug"; then
  git worktree add --quiet "$intwt" "impl/$slug" || fail "git worktree add of the existing impl/$slug failed"
else
  git worktree add --quiet -b "impl/$slug" "$intwt" "$main" || fail "git worktree add -b impl/$slug failed"
fi

echo "ROOT=$root"
echo "SLUG=$slug"
echo "MAIN=$main"
echo "REMOTE=$remote"
echo "BASE=$(git rev-parse "$main")"
echo "GIT=$(command -v git)"
echo "PR_MODE=$pr_mode"
echo "PROFILE=$profile"
echo "CODEGRAPH=$codegraph"
echo "IMPL=$root/$impl"
echo "BOARD=$root/$impl/BOARD.md"
echo "INTWT=$intwt"
echo "ENV OK"
