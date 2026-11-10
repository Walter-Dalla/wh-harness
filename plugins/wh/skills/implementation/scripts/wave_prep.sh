#!/usr/bin/env bash
# Builds the WAVE attachment of a /wh:implementation wave and says whether the enricher is needed.
#
#   wave_prep.sh <slug> <wave> <base> <lane>…
#
# Run at the repository root. <wave> = W<n>; <base> = the hash the previous wave was born from; <lane>… = the lanes
# still to dispatch, each with .impl/<slug>/<lane>.md. Works on the integration worktree
# .claude/worktrees/impl-<slug> (its HEAD is the tip):
#   1. every Acceptance of each lane at the tip (acceptance.py; green = a line with ` · exit 0 · `);
#   2. the CONTRACT lines of .impl/<slug>/BOARD.md after the last WAVE line (all of them without a WAVE line);
#   3. the files moved in <base>..HEAD, and per lane the OWN:/MAY: lines of `scope.sh --classify`.
# Writes .impl/<slug>/wave-<wave>.md (a title and four sections, `—` when empty) and prints its path, then
# `WAVE CLEAN` (exit 0) or `WAVE ENRICHER: <g> green item(s), <c> CONTRACT line(s), <o> owned file(s) moved` (exit 3).
# Exit 1 with `WAVE_PREP FAILED: <reason>`: bad call, not the root, integration worktree, lane file or board
# missing, unknown base.
set -u

fail() { echo "WAVE_PREP FAILED: $*"; exit 1; }

[ $# -ge 4 ] || fail "usage: wave_prep.sh <slug> <wave> <base> <lane>…"
slug=$1; wave=$2; base=$3; shift 3
case $slug in *[!a-z0-9-]*|'') fail "slug '$slug' is not kebab-case" ;; esac
[[ $wave =~ ^W[0-9]+$ ]] || fail "wave '$wave' is not W<n>"

root=$(git rev-parse --show-toplevel 2>/dev/null) || fail "not inside a git repository"
[ "$root" = "$(pwd -P)" ] || fail "run at the repository root ($root), not in $(pwd -P)"
scripts=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd) || fail "cannot resolve the scripts folder"
impl=$root/.impl/$slug
intwt=$root/.claude/worktrees/impl-$slug
board=$impl/BOARD.md
[ -d "$intwt" ] || fail "integration worktree $intwt missing"
[ -f "$board" ] || fail "board $board missing"
for lane in "$@"; do
  [ -f "$impl/$lane.md" ] || fail "lane file $impl/$lane.md missing"
done
git -C "$intwt" rev-parse --verify -q "$base^{commit}" >/dev/null || fail "base $base unknown"
tip=$(git -C "$intwt" rev-parse HEAD) || fail "no HEAD in $intwt"

accept=; green=0
for lane in "$@"; do
  # stdout only: acceptance.py may print warnings on stderr.
  out=$(python3 -I "$scripts/acceptance.py" "$impl/$lane.md" "$intwt" 2>/dev/null)
  accept+="### $lane"$'\n'"$out"$'\n'
  while IFS= read -r line; do
    [[ $line == *' · exit 0 · '* ]] && green=$((green + 1))
  done <<< "$out"
done

contract=$(awk -F'|' '{ kind = $3; gsub(/^[ \t]+|[ \t]+$/, "", kind) }
  kind == "WAVE" { n = 0; next }
  kind == "CONTRACT" { lines[++n] = $0 }
  END { for (i = 1; i <= n; i++) print lines[i] }' "$board")
ncontract=0
[ -z "$contract" ] || ncontract=$(( $(printf '%s\n' "$contract" | wc -l) ))

moved=$(git -C "$intwt" -c core.quotepath=off diff --no-color --no-ext-diff --name-status "$base..HEAD") \
  || fail "git diff $base..HEAD failed in $intwt"

owned=; nowned=0
for lane in "$@"; do
  out=$(cd "$intwt" && bash "$scripts/scope.sh" --classify "$impl/$lane.md" "$base" HEAD) \
    || fail "scope.sh --classify failed for $lane: $out"
  while IFS= read -r line; do
    case $line in
      OWN:*|MAY:*) owned+="$lane · $line"$'\n'; nowned=$((nowned + 1)) ;;
    esac
  done <<< "$out"
done

body() { if [ -n "$1" ]; then printf '%s\n' "${1%$'\n'}"; else echo —; fi; }

file=$impl/wave-$wave.md
{
  echo "# WAVE $wave · $slug · base $base · tip $tip"
  echo
  echo "## Acceptance at the tip"
  body "$accept"
  echo
  echo "## CONTRACT lines of the board"
  body "$contract"
  echo
  echo "## Moved files"
  body "$moved"
  echo
  echo "## Moved files inside a pending lane"
  body "$owned"
} > "$file" || fail "cannot write $file"

echo "$file"
if [ "$green" -eq 0 ] && [ "$ncontract" -eq 0 ] && [ "$nowned" -eq 0 ]; then
  echo "WAVE CLEAN"
  exit 0
fi
echo "WAVE ENRICHER: $green green item(s), $ncontract CONTRACT line(s), $nowned owned file(s) moved"
exit 3
