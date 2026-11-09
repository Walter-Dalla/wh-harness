#!/usr/bin/env bash
# Intake of /wh:implementation, deterministic: decides between a pending-file intake and a raw-text intake,
# resolves the pending files and the slug, or gives the next free pending id. `KEY=VALUE` lines on stdout.
#
#   intake.sh <root> [<P-NNN | path.md | text>…]    PENDING_DIR=, INTAKE=file|raw, PENDING=, SLUG=, INTAKE OK
#   intake.sh <root> next                          P-NNN (highest id in the pending folder + 1)
#
# Pending folder: the first backticked path of the `## Pending` section of <root>/.claude/profile/_common.md,
# else docs/pending/; relative to <root>, created when missing. With no argument, every P-*.md whose first 10
# lines hold `status: open`. Every token resolved (an id with exactly one P-NNN-*.md, or a .md inside the
# folder) = file intake; any other token = raw intake, the resolved files listed as merge targets.
set -u

fail() { echo "INTAKE FAILED: $*"; exit 1; }
usage() { echo "INTAKE FAILED: usage: intake.sh <root> [<P-NNN | path.md | text>…] | intake.sh <root> next"; exit 2; }

[ $# -ge 1 ] || usage
[ -d "$1" ] || usage
root=$(cd "$1" && pwd -P) || usage
shift

rel=
common=$root/.claude/profile/_common.md
if [ -f "$common" ]; then
  rel=$(awk '/^## /{ if (insec) exit; insec = ($0 ~ /^## Pending[[:space:]]*$/); next }
             insec && match($0, /`[^`]+`/) { print substr($0, RSTART + 1, RLENGTH - 2); exit }' "$common")
fi
[ -n "$rel" ] || rel=docs/pending/
case $rel in /*) dir=$rel ;; *) dir=$root/$rel ;; esac
mkdir -p "$dir" || fail "cannot create $dir"
dir=$(cd "$dir" && pwd -P) || fail "cannot enter $dir"

if [ $# -eq 1 ] && [ "$1" = next ]; then
  high=0
  for f in "$dir"/P-[0-9][0-9][0-9]*.md; do
    [ -e "$f" ] || continue
    n=${f##*/P-}; n=${n:0:3}
    [ $((10#$n)) -gt "$high" ] && high=$((10#$n))
  done
  printf 'P-%03d\n' $((high + 1))
  exit 0
fi

found=()
intake=file
if [ $# -eq 0 ]; then
  for f in "$dir"/P-*.md; do
    [ -f "$f" ] || continue
    head -n 10 "$f" | grep -q '^status: open' && found+=("$f")
  done
  [ ${#found[@]} -gt 0 ] || fail "no open pending file in $dir"
else
  for tok in "$@"; do
    hit=
    if [[ $tok =~ ^P-[0-9]{3}$ ]]; then
      matches=()
      for f in "$dir/$tok"-*.md; do [ -f "$f" ] && matches+=("$f"); done
      [ ${#matches[@]} -eq 1 ] && hit=${matches[0]}
    elif [[ $tok == *.md ]]; then
      case $tok in /*) path=$tok ;; *) path=$root/$tok ;; esac
      if [ -f "$path" ]; then
        parent=$(cd "$(dirname "$path")" && pwd -P)
        [ "$parent" = "$dir" ] && hit=$dir/$(basename "$path")
      fi
    fi
    if [ -n "$hit" ]; then found+=("$hit"); else intake=raw; fi
  done
fi

pending=
if [ ${#found[@]} -gt 0 ]; then
  pending=$(printf '%s\n' "${found[@]}" | LC_ALL=C sort -u | tr '\n' ' ')
  pending=${pending% }
fi
read -r -a list <<< "$pending"

slug=—
if [ "$intake" = file ]; then
  if [ ${#list[@]} -eq 1 ]; then
    slug=$(basename "${list[0]}" .md); slug=${slug#P-[0-9][0-9][0-9]-}
  else
    first=$(basename "${list[0]}"); last=$(basename "${list[${#list[@]} - 1]}")
    slug=pending-${first:2:3}-${last:2:3}
  fi
fi

echo "PENDING_DIR=$dir"
echo "INTAKE=$intake"
echo "PENDING=$pending"
echo "SLUG=$slug"
echo "INTAKE OK"
