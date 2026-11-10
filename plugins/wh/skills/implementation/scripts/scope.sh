#!/usr/bin/env bash
# Checks that a /wh:implementation lane only changed the files it owns.
# Usage: scope.sh <lane file> <base> [<ref>=HEAD]
#        scope.sh --classify <lane file> <base> [<ref>=HEAD]
# Reads from the lane file the lines "Owns:", "May touch" and "Union:" (paths or globs in backticks; `*` crosses folders).
# "Union:" are the profile's union files (§ Union files), which every lane may append to.
# Output: one line per file outside the scope ("OUTSIDE: …", exit 1) and the "May touch" ones ("WARNING expected: …").
# --classify: one line per changed file, "OWN: …", "UNION: …", "MAY: …" or "OUTSIDE: …" (same precedence), exit 0.
set -u
classify=0
if [ "${1:-}" = --classify ]; then classify=1; shift; fi
lane=${1:?lane file}; base=${2:?base}; ref=${3:-HEAD}
[ -r "$lane" ] || { echo "SCOPE FAILED: lane file unreadable: $lane"; exit 2; }

# Only the lane header (before the first "## "); the three labels may share one line.
head=$(sed -n '1,/^## /p' "$lane")
# A path ending in `/` means the whole folder.
globs() { grep -E "$1" <<< "$head" | sed -E "$2" | grep -o '`[^`]*`' | tr -d '`' | sed 's|/$|/*|'; }
mapfile -t own < <(globs '^Owns:' 's/(May touch|Union:).*//')
mapfile -t may < <(globs 'May touch' 's/.*May touch[^`]*//; s/Union:.*//')
mapfile -t union < <(globs 'Union:' 's/.*Union://')
[ ${#own[@]} -gt 0 ] || { echo "SCOPE FAILED: no path in backticks on the 'Owns:' line of $lane"; exit 2; }

# shellcheck disable=SC2053  # the right-hand side is a glob on purpose
# `X/**/*.cs` also matches `X/a.cs` (the `**/` accepts zero folders); Godot's `<file>.uid` follows the file's owner.
matches() {
  local f=$1; shift; local g
  for g in "$@"; do
    [[ $f == "$g" ]] && return 0  # literal: path with a glob character (`app/[id]/page.tsx`)
    [[ $f == $g ]] && return 0
    [[ $f == ${g//\*\*\//} ]] && return 0
    [[ $f == *.uid && ${f%.uid} == $g ]] && return 0
  done
  return 1
}

# quotepath=off: a name with accents comes out as is, not escaped in quotes.
changed() { git -c core.quotepath=off diff --name-only "$base...$ref"; }

if [ $classify -eq 1 ]; then
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    if matches "$f" "${own[@]}"; then echo "OWN: $f"
    elif [ ${#union[@]} -gt 0 ] && matches "$f" "${union[@]}"; then echo "UNION: $f"
    elif [ ${#may[@]} -gt 0 ] && matches "$f" "${may[@]}"; then echo "MAY: $f"
    else echo "OUTSIDE: $f"
    fi
  done < <(changed)
  exit 0
fi

out=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  if matches "$f" "${own[@]}"; then continue
  elif [ ${#union[@]} -gt 0 ] && matches "$f" "${union[@]}"; then continue
  elif [ ${#may[@]} -gt 0 ] && matches "$f" "${may[@]}"; then echo "WARNING expected: $f"
  else echo "OUTSIDE: $f"; out=1
  fi
done < <(changed)

[ $out -eq 0 ] && echo "SCOPE OK: $(changed | wc -l) files inside the lane"
exit $out
