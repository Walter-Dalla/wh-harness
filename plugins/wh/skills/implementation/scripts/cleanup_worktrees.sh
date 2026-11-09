#!/usr/bin/env bash
# Removes the worktrees of one /wh:implementation run, saving what they still hold (cleanup skill § 6, phase 6.4).
#
#   cleanup_worktrees.sh <root> <slug> [--main <branch>] [--integration] [--dry-run]
#
# A worktree belongs to the run when its branch is `impl/<slug>-*`, or `worktree-agent-*` with a HEAD that is a
# commit of `<main>..impl/<slug>`. The integration worktree (branch `impl/<slug>`) only goes with --integration
# (after the push and the PR). Every other worktree stays and is listed as `KEPT`. For each one of the run: local
# changes become a commit `wip: <branch>` on its branch; then `git worktree remove`, `git branch -D` of a
# `worktree-agent-*` branch (the `impl/…` branches stay), and `git worktree prune` at the end.
set -u

[ $# -ge 2 ] || { echo "CLEANUP FAILED: usage: cleanup_worktrees.sh <root> <slug> [--main <branch>] [--integration] [--dry-run]"; exit 2; }
root=$1; slug=$2; shift 2
main=main; integration=0; dry=0
while [ $# -gt 0 ]; do
  case $1 in
    --main) main=${2:?--main without a value}; shift 2 ;;
    --integration) integration=1; shift ;;
    --dry-run) dry=1; shift ;;
    *) echo "CLEANUP FAILED: unknown option $1"; exit 2 ;;
  esac
done
g() { git -C "$root" "$@"; }
g rev-parse --show-toplevel >/dev/null 2>&1 || { echo "CLEANUP FAILED: $root is not a git repository"; exit 1; }
root=$(g rev-parse --show-toplevel)
has_integration=0
g show-ref --verify --quiet "refs/heads/impl/$slug" && has_integration=1

removed=0
wt=''; head=''; branch=''
flush() {
  [ -n "$wt" ] || return 0
  [ "$wt" != "$root" ] || return 0
  local short=${branch#refs/heads/} mine=0 agent=0
  case $short in
    "impl/$slug-"*) mine=1 ;;
    "impl/$slug") [ "$integration" = 1 ] && mine=1 ;;
    worktree-agent-*)
      agent=1
      if [ "$has_integration" = 1 ] && g merge-base --is-ancestor "$head" "impl/$slug" 2>/dev/null \
         && ! g merge-base --is-ancestor "$head" "$main" 2>/dev/null; then mine=1; fi ;;
  esac
  if [ "$mine" != 1 ]; then echo "KEPT: $wt (${short:-detached})"; return 0; fi
  if [ "$dry" = 1 ]; then echo "WOULD REMOVE: $wt ($short)"; return 0; fi
  if [ -n "$(git -C "$wt" status --porcelain 2>/dev/null)" ]; then
    if [ -z "$short" ]; then git -C "$wt" switch -q -c "wt/$(basename "$wt")"; short="wt/$(basename "$wt")"; fi
    git -C "$wt" add -A && git -C "$wt" commit -q -m "wip: $short" && echo "SAVED: wip: $short $(git -C "$wt" rev-parse --short HEAD)"
  fi
  g worktree unlock "$wt" >/dev/null 2>&1 || true
  if g worktree remove --force "$wt" 2>/dev/null; then
    echo "REMOVED: $wt ($short)"; removed=$((removed + 1))
    if [ "$agent" = 1 ] && [ -n "$short" ]; then g branch -D "$short" >/dev/null 2>&1 && echo "BRANCH DELETED: $short"; fi
  else
    echo "CLEANUP WARNING: could not remove $wt"
  fi
}
while IFS= read -r line; do
  case $line in
    "worktree "*) flush; wt=${line#worktree }; head=''; branch='' ;;
    "HEAD "*) head=${line#HEAD } ;;
    "branch "*) branch=${line#branch } ;;
    "") ;;
  esac
done < <(g worktree list --porcelain)
flush
[ "$dry" = 1 ] || g worktree prune
echo "CLEANUP OK: $removed worktree(s) removed"
