#!/usr/bin/env bash
# The deterministic half of /wh:quick: a one-commit change in its own worktree, with a size gate that sends
# anything larger to /wh:implementation.
#
#   quick.sh start  <slug> [--main <b>=main] [--remote <r>=origin]
#   quick.sh gate   <worktree> [--main <b>] [--remote <r>] [--max-files <n>=3] [--max-lines <n>=40]
#   quick.sh finish <worktree> [--main <b>] [--remote <r>] [--max-files <n>] [--max-lines <n>] [--body <text>]
#   quick.sh drop   <worktree>
#
# start: at the repository root, any branch, local changes allowed (the clone's checkout is never touched).
#   Fetches <remote>/<main>, creates <root>/.claude/worktrees/quick-<slug> on the new branch quick/<slug> born
#   from it, and prints ROOT=, WT=, BRANCH=, BASE=, MAIN=, REMOTE=, GIT=, PR_MODE=github|none, PROFILE=ok|missing
#   and `QUICK OK`.
# gate: the change of <worktree> against its merge base with <remote>/<main>, committed or not. `QUICK OK: <n>
#   file(s), <m> line(s)` (exit 0), or `QUICK ESCALATE: <reasons>` (exit 3) when it has more than --max-files
#   files or --max-lines changed lines, adds, deletes or renames a file, touches a binary file, changes a file mode or type, or touches a path
#   the profile's `## Contract` section names in backticks (a token is a path, a glob or a folder) (<worktree>/.claude/profile/implementation.md).
# finish: needs a clean worktree with at least one commit; runs the gate again (escalate = exit 3, nothing
#   pushed), pushes quick/<slug>, opens the PR when `gh` reaches a GitHub repository (`PR=<url>`; --body replaces
#   the commit message as its body) or prints `PR=none` and `MERGE=<command>`, removes the worktree (a failed `gh pr create` = QUICK FAILED, the
#   branch pushed and the worktree kept) (the branch
#   stays) and prints `QUICK DONE`.
# drop: removes the worktree and deletes its local quick/* branch (an abandoned or escalated attempt).
# Exit 1 with `QUICK FAILED: <reason>` on a bad call or a failed git step; nothing is pushed after a failure.
set -u

fail() { echo "QUICK FAILED: $*"; exit 1; }
usage() { fail "usage: quick.sh start <slug> | gate <worktree> | finish <worktree> | drop <worktree> [--main <b>] [--remote <r>] [--max-files <n>] [--max-lines <n>] [--body <text>]"; }

[ $# -ge 2 ] || usage
cmd=$1; target=$2; shift 2
main=main; remote=origin; max_files=3; max_lines=40; body=
while [ $# -gt 0 ]; do
  case $1 in
    --main|--remote|--max-files|--max-lines|--body)
      [ $# -ge 2 ] && [ -n "$2" ] || fail "$1 without a value" ;;
    *) fail "unknown option $1" ;;
  esac
  case $1 in
    --main) main=$2 ;;
    --remote) remote=$2 ;;
    --max-files) max_files=$2 ;;
    --max-lines) max_lines=$2 ;;
    --body) body=$2 ;;
  esac
  shift 2
done
case $max_files$max_lines in *[!0-9]*) fail "--max-files and --max-lines are numbers" ;; esac

# Backticked tokens of the profile's `## Contract` section, one per line.
contract_paths() {
  local profile=$1/.claude/profile/implementation.md
  [ -f "$profile" ] || return 0
  awk '/^## /{on = ($0 == "## Contract")} on' "$profile" | grep -o '`[^`]*`' | tr -d '`'
}

# Prints the verdict line of the gate for worktree $1; returns 0 (ok), 3 (escalate) or 1 (failed).
gate() {
  local wt=$1 base files=0 lines=0 reasons='' added deleted path status pat
  git -C "$wt" rev-parse --verify -q "$remote/$main^{commit}" >/dev/null || { echo "QUICK FAILED: $remote/$main missing in $wt"; return 1; }
  base=$(git -C "$wt" merge-base HEAD "$remote/$main") || { echo "QUICK FAILED: no merge base with $remote/$main"; return 1; }
  if [ -n "$(git -C "$wt" ls-files --others --exclude-standard)" ]; then reasons="$reasons; adds a file"; fi
  while IFS=$'\t' read -r status path _; do
    [ -n "$status" ] || continue
    case $status in M*|T*) ;; *) reasons="$reasons; adds, deletes or renames a file ($path)" ;; esac
  done < <(git -C "$wt" -c core.quotepath=off diff --name-status "$base")
  while read -r oldmode newmode _; do
    [ "$oldmode" = "$newmode" ] || { reasons="$reasons; changes a file mode or type"; break; }
  done < <(git -C "$wt" diff --raw "$base" | tr -d ':')
  while IFS=$'\t' read -r added deleted path; do
    [ -n "$path" ] || continue
    files=$((files + 1))
    if [ "$added" = - ]; then reasons="$reasons; binary file ($path)"; continue; fi
    lines=$((lines + added + deleted))
    while IFS= read -r pat; do
      [ -n "$pat" ] || continue
      pat=${pat%/}
      # shellcheck disable=SC2053  # the right side is a glob on purpose
      if [ "$path" = "$pat" ] || [[ $path == $pat ]] || [[ $path == $pat/* ]]; then
        reasons="$reasons; contract path ($path)"; break
      fi
    done < <(contract_paths "$wt")
  done < <(git -C "$wt" -c core.quotepath=off diff --numstat "$base")
  if [ "$files" -eq 0 ] && [ -z "$reasons" ]; then echo "QUICK FAILED: no change in $wt"; return 1; fi
  [ "$files" -le "$max_files" ] || reasons="$reasons; $files files (limit $max_files)"
  [ "$lines" -le "$max_lines" ] || reasons="$reasons; $lines changed lines (limit $max_lines)"
  if [ -n "$reasons" ]; then echo "QUICK ESCALATE: ${reasons#; }"; return 3; fi
  echo "QUICK OK: $files file(s), $lines line(s)"
}

quick_worktree() {
  [ -d "$target" ] || fail "worktree $target missing"
  branch=$(git -C "$target" branch --show-current 2>/dev/null) || fail "$target is not a git worktree"
  case $branch in quick/*) ;; *) fail "$target is on '$branch', not a quick/* branch" ;; esac
}

case $cmd in
  start)
    slug=$target
    case $slug in *[!a-z0-9-]*|''|-*|*-) fail "slug '$slug' is not kebab-case" ;; esac
    root=$(git rev-parse --show-toplevel 2>/dev/null) || fail "not inside a git repository"
    [ "$root" = "$(pwd -P)" ] || fail "run at the repository root ($root), not in $(pwd -P)"
    [ "$(git rev-parse --git-dir)" = .git ] || fail "run in the main checkout, not inside a worktree"
    git fetch -q "$remote" "$main" >/dev/null 2>&1 || fail "git fetch $remote $main failed (gh auth setup-git?)"
    wt=$root/.claude/worktrees/quick-$slug
    [ ! -e "$wt" ] || fail "$wt already exists (quick.sh drop it, or pick another slug)"
    git show-ref --verify --quiet "refs/heads/quick/$slug" && fail "branch quick/$slug already exists"
    exclude=$(git rev-parse --git-path info/exclude)
    mkdir -p "$(dirname "$exclude")"; touch "$exclude"
    grep -qxF .claude/worktrees/ "$exclude" || printf '%s\n' .claude/worktrees/ >> "$exclude"
    git worktree add --quiet -b "quick/$slug" "$wt" "$remote/$main" || fail "git worktree add -b quick/$slug failed"
    pr_mode=none
    if command -v gh >/dev/null 2>&1 && gh repo view --json nameWithOwner >/dev/null 2>&1; then pr_mode=github; fi
    profile=ok
    [ -f "$wt/.claude/profile/implementation.md" ] || profile=missing
    echo "ROOT=$root"
    echo "WT=$wt"
    echo "BRANCH=quick/$slug"
    echo "BASE=$(git -C "$wt" rev-parse HEAD)"
    echo "MAIN=$main"
    echo "REMOTE=$remote"
    echo "GIT=$(command -v git)"
    echo "PR_MODE=$pr_mode"
    echo "PROFILE=$profile"
    echo "QUICK OK"
    ;;
  gate)
    [ -d "$target" ] || fail "worktree $target missing"
    gate "$target"; exit $?
    ;;
  finish)
    quick_worktree
    [ -z "$(git -C "$target" status --porcelain)" ] || fail "uncommitted changes in $target (commit first)"
    [ "$(git -C "$target" rev-list --count "$remote/$main..HEAD")" -gt 0 ] || fail "no commit on $branch"
    gate "$target" || exit $?
    git -C "$target" push -q -u "$remote" "$branch" >/dev/null 2>&1 || fail "git push $remote $branch failed"
    pr=none
    if command -v gh >/dev/null 2>&1 && (cd "$target" && gh repo view --json nameWithOwner >/dev/null 2>&1); then
      # The verdict is gh's own exit, never a filter's: a failed PR keeps the worktree and says so.
      if [ -n "$body" ]; then
        title=$(git -C "$target" log -1 --format=%s)
        out=$(cd "$target" && gh pr create --base "$main" --head "$branch" --title "$title" --body "$body" 2>&1)
      else
        out=$(cd "$target" && gh pr create --base "$main" --head "$branch" --fill 2>&1)
      fi
      # shellcheck disable=SC2181  # the assignment above is one of two branches
      [ $? -eq 0 ] || fail "gh pr create failed ($branch is pushed, worktree kept): $(tail -n 1 <<< "$out")"
      pr=$(tail -n 1 <<< "$out")
    fi
    echo "BRANCH=$branch"
    echo "PR=$pr"
    [ "$pr" != none ] || echo "MERGE=git switch $main && git merge --no-ff $branch && git push $remote $main"
    git -C "$target" worktree remove "$target" >/dev/null 2>&1 || echo "WARNING: worktree $target not removed"
    echo "QUICK DONE"
    ;;
  drop)
    quick_worktree
    common=$(cd "$target" && cd "$(git rev-parse --git-common-dir)" && pwd -P) || fail "cannot resolve the repository of $target"
    cd "$common" || fail "cannot enter $common"   # the caller may be standing inside the worktree being removed
    git --git-dir "$common" worktree remove --force "$target" >/dev/null 2>&1 || fail "git worktree remove $target failed"
    git --git-dir "$common" branch -q -D "$branch" >/dev/null 2>&1 || fail "git branch -D $branch failed"
    echo "QUICK DROPPED: $branch"
    ;;
  *) usage ;;
esac
