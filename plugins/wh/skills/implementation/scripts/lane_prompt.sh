#!/usr/bin/env bash
# Prints the dispatch prompt of a /wh:implementation lane or QA, with the same labels the agents read, and writes
# the code QA diff. Stdout is the prompt and nothing else.
#
#   lane_prompt.sh <slug> <lane> [--qa] [--remote <r>=origin] [--main <b>=main] [--continuation <text>]
#                  [--retest <ids>] [--areas <text>] [--verify <ids>] [--gates yes|no]
#
# Run at the repository root (any branch). Without --qa: the lane prompt (needs .impl/<slug>/<lane>.md and the
# branch impl/<slug>; the port is the word after `port ` on the lane file's first line, else —).
# --qa with a lane: fetches <remote>, writes `git diff <merge-base>...<remote>/impl/<slug>-<lane>` to
# .impl/<slug>/qa/<lane>.diff and prints the code QA prompt. --qa code: the same over <remote>/impl/<slug> against
# <main> (no lane file). --qa final: fetches and prints the final QA prompt (no diff).
# Exit 1 with `LANE_PROMPT FAILED: <reason>`: bad call, not the root, lane file missing, ref missing.
set -u

fail() { echo "LANE_PROMPT FAILED: $*"; exit 1; }
usage() { fail "usage: lane_prompt.sh <slug> <lane> [--qa] [--remote <r>] [--main <b>] [--continuation <text>] [--retest <ids>] [--areas <text>] [--verify <ids>] [--gates yes|no]"; }

[ $# -ge 2 ] || usage
slug=$1; lane=$2; shift 2
case $slug in *[!a-z0-9-]*|'') fail "slug '$slug' is not kebab-case" ;; esac
case $lane in *[!A-Za-z0-9_-]*|'') fail "lane '$lane' is not a lane name" ;; esac

qa=0; remote=origin; main=main
continuation='from scratch'; retest=no; areas=none; verify=—; gates=no
while [ $# -gt 0 ]; do
  case $1 in
    --qa) qa=1; shift; continue ;;
    --remote|--main|--continuation|--retest|--areas|--verify|--gates)
      [ $# -ge 2 ] && [ -n "$2" ] || fail "$1 without a value" ;;
    *) fail "unknown option $1" ;;
  esac
  case $1 in
    --remote) remote=$2 ;;
    --main) main=$2 ;;
    --continuation) continuation=$2 ;;
    --retest) retest=$2 ;;
    --areas) areas=$2 ;;
    --verify) verify=$2 ;;
    --gates) gates=$2 ;;
  esac
  shift 2
done
case $gates in yes|no) ;; *) fail "--gates is yes or no, not '$gates'" ;; esac

# The template ends each free text with a period: one already at the end is not doubled.
continuation=${continuation%.}; retest=${retest%.}; areas=${areas%.}; verify=${verify%.}

root=$(git rev-parse --show-toplevel 2>/dev/null) || fail "not inside a git repository"
[ "$root" = "$(pwd -P)" ] || fail "run at the repository root ($root), not in $(pwd -P)"
plugin=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd) || fail "cannot resolve the plugin root"
gitbin=$(command -v git)
impl=$root/.impl/$slug
profile="Profile: $root/.claude/profile/implementation.md and _common.md."
lanefile=$impl/$lane.md

rev() { got=$(git rev-parse --verify -q "$1^{commit}") || fail "ref $1 missing"; }

if [ "$qa" = 0 ]; then
  [ -f "$lanefile" ] || fail "lane file $lanefile missing"
  rev "impl/$slug"; tip=$got
  first=$(head -n 1 "$lanefile")
  port=—
  if [[ $first =~ (^|[[:space:]])port[[:space:]]+([^[:space:]]+) ]]; then port=${BASH_REMATCH[2]}; fi
  echo "PLUGIN_ROOT=$plugin"
  echo "Lane: $lane. File: $lanefile. Repo: $root. $profile"
  echo "Branch: impl/$slug-$lane. Base: impl/$slug @ $tip. Remote: $remote."
  echo "Commands: profile § Worktree commands before the 1st command; git = $gitbin -C <worktree> …, one command per call."
  echo "Port: $port. Board: $impl/BOARD.md."
  echo "Retro: $impl/retros/$lane.md. Checkpoint: $impl/progress/$lane.md."
  echo "Continuation: $continuation."
  exit 0
fi

case $lane in code|final) ;; *) [ -f "$lanefile" ] || fail "lane file $lanefile missing" ;; esac
git fetch -q "$remote" >/dev/null 2>&1 || fail "git fetch $remote failed"

if [ "$lane" = final ]; then
  rev "$remote/impl/$slug"; tip=$got
  echo "PLUGIN_ROOT=$plugin"
  echo "Mode: final. Task: $slug. Repo: $root. $profile Plan: $impl/PLAN.md."
  echo "Branch: impl/$slug @ $tip. Diff base: $main. Remote: $remote. Touched areas: $areas."
  echo "Output: $impl/qa/final.md. Retro: $impl/retros/qa-final.md."
  echo "Commands: profile § Worktree commands before the 1st command; git = $gitbin -C <worktree> …, one command per call."
  echo "Retest: $retest."
  echo "Verify: $verify."
  echo "Gates: $gates."
  exit 0
fi

if [ "$lane" = code ]; then
  ref=$remote/impl/$slug; branch=impl/$slug; from=$main; lanelabel=all
else
  ref=$remote/impl/$slug-$lane; branch=impl/$slug-$lane; from=impl/$slug; lanelabel=$lanefile
fi
rev "$ref"; tip=$got
rev "$from"
base=$(git merge-base "$from" "$ref") || fail "no merge base between $from and $ref"
mkdir -p "$impl/qa" || fail "cannot create $impl/qa"
diff=$impl/qa/$lane.diff
git -c core.quotepath=off diff --no-color --no-ext-diff --src-prefix=a/ --dst-prefix=b/ "$base...$ref" > "$diff" \
  || fail "git diff $base...$ref failed"

echo "PLUGIN_ROOT=$plugin"
echo "Mode: code. Task: $slug. Repo: $root. $profile Plan: $impl/PLAN.md. Lane: $lanelabel."
echo "Branch: $branch @ $tip. Diff base: $base. Remote: $remote. Diff: $diff."
echo "Output: $impl/qa/$lane.md. Retro: $impl/retros/qa-$lane.md."
echo "Commands: git = $gitbin -C $root …, one command per call."
echo "Retest: $retest."
