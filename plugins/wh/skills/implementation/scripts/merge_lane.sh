#!/usr/bin/env bash
# Merges a lane branch into the integration branch of a /wh:implementation task, and only there.
#
#   merge_lane.sh <integration worktree> <slug> <lane> <remote> [<main>]
#
# Refuses (exit 1) when the worktree is not on `impl/<slug>`, is dirty, or the lane branch is not on the remote:
# the clone's main checkout never receives a merge (LANES.md §3). Fetches, merges `<remote>/impl/<slug>-<lane>`
# with --no-ff, prints `MERGED: <lane> -> <hash>`. A conflict leaves the merge in progress and exits 3 with
# `MERGE CONFLICT: <files>`. After the merge, `MAIN MOVED: <n> commit(s) on <remote>/<main> not in impl/<slug>`
# warns that the main branch advanced since the base (exit stays 0; the orchestrator notes it on the board).
set -u

if [ $# -lt 4 ]; then
  echo "MERGE FAILED: usage: merge_lane.sh <integration worktree> <slug> <lane> <remote> [<main>]"
  exit 2
fi
wt=$1; slug=$2; lane=$3; remote=$4; main=${5:-main}
target="impl/$slug"
lane_ref="refs/remotes/$remote/impl/$slug-$lane"

if ! current=$(git -C "$wt" branch --show-current 2>/dev/null); then
  echo "MERGE REFUSED: $wt is not a git worktree"
  exit 1
fi
if [ "$current" != "$target" ]; then
  echo "MERGE REFUSED: $wt is on '${current:-detached HEAD}', not $target (integration only happens on $target, in its own worktree)"
  exit 1
fi
if [ -n "$(git -C "$wt" status --porcelain --untracked-files=no)" ]; then
  echo "MERGE REFUSED: $wt has local changes; commit or stash them first"
  exit 1
fi
if ! git -C "$wt" fetch --quiet "$remote"; then
  echo "MERGE REFUSED: git fetch $remote failed"
  exit 1
fi
if ! git -C "$wt" rev-parse --verify --quiet "$lane_ref" >/dev/null; then
  echo "MERGE REFUSED: $remote/impl/$slug-$lane does not exist (the lane did not push)"
  exit 1
fi

if ! git -C "$wt" merge --no-ff "$lane_ref" -m "impl: $lane" >/dev/null 2>&1; then
  conflicts=$(git -C "$wt" diff --name-only --diff-filter=U | tr '\n' ' ')
  echo "MERGE CONFLICT: ${conflicts:-see git status} (merge left in progress; resolve or git merge --abort)"
  exit 3
fi
echo "MERGED: $lane -> $(git -C "$wt" rev-parse --short HEAD)"

main_ref="refs/remotes/$remote/$main"
if git -C "$wt" rev-parse --verify --quiet "$main_ref" >/dev/null; then
  moved=$(git -C "$wt" rev-list --count "HEAD..$main_ref")
  if [ "$moved" -gt 0 ]; then
    echo "MAIN MOVED: $moved commit(s) on $remote/$main not in $target ($(git -C "$wt" diff --stat "HEAD...$main_ref" | tail -1 | sed 's/^ *//'))"
  fi
else
  echo "MERGE WARNING: $remote/$main not found; main-moved check skipped"
fi
exit 0
