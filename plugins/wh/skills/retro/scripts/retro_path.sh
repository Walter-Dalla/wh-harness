#!/usr/bin/env bash
# Path of a new retro file of /wh:retro: <clone root>/retro/<YYYY-MM-DD-HHMMSS>[-<label>].md (local time, now).
#
#   retro_path.sh [<label>]     prints the absolute path; creates retro/ and keeps it out of git
#
# Clone root = the main worktree of the cwd's repository (an agent worktree resolves to its clone, so the file
# outlives the worktree); outside git, the cwd. A retro/ that git does not ignore yet gets `/retro/` in
# .git/info/exclude; the line in .gitignore is the repo's (/wh:adopt adds it, check.py validates it).
set -u

fail() { echo "RETRO FAILED: $*"; exit 1; }

[ $# -le 1 ] || fail "usage: retro_path.sh [<label>]"
label=${1:-}
[[ $label =~ ^[A-Za-z0-9._-]*$ ]] || fail "label takes letters, digits, '.', '_' and '-', not '$label'"

root=$(git worktree list --porcelain 2>/dev/null | sed -n '1s/^worktree //p')
ingit=yes
[ -n "$root" ] && [ -d "$root" ] || { root=$(pwd -P); ingit=no; }
dir=$root/retro
mkdir -p "$dir" || fail "cannot create $dir"

if [ "$ingit" = yes ]; then
  git -C "$root" check-ignore -q retro
  if [ $? -eq 1 ]; then
    exclude=$(git -C "$root" rev-parse --git-path info/exclude) || fail "cannot find .git/info/exclude"
    case $exclude in /*) ;; *) exclude=$root/$exclude ;; esac
    mkdir -p "$(dirname "$exclude")" && echo '/retro/' >> "$exclude" || fail "cannot write $exclude"
  fi
fi

echo "$dir/$(date +%Y-%m-%d-%H%M%S)${label:+-$label}.md"
