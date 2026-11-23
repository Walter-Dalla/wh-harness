#!/usr/bin/env bash
# Intake of /wh:implementation, deterministic: decides between a pending-file intake and a raw-text intake,
# resolves the pending files and the slug, or gives the next free pending id. `KEY=VALUE` lines on stdout.
#
#   intake.sh <root> [--dir <folder>] [<P-NNN | path.md | text>…]   PENDING_DIR=, INTAKE=file|raw, PENDING=, SLUG=, INTAKE OK
#   intake.sh <root> [--dir <folder>] --next                       P-NNN (highest id in the folder, its done/ or the git history + 1)
#
# Pending folder: <root>/pending/, always; `--dir <folder>` (relative to <root>, or absolute) redirects this call to a
# folder the owner named, which must exist. pending/ is created when missing, is local to the clone and never
# committed: when git does not ignore it yet, it goes in .git/info/exclude (the line in .gitignore is the repo's:
# /wh:adopt adds it). Landed files move to the done/ subfolder. With no argument, every P-*.md whose first 10
# lines hold the line `status: open`. Every token resolved (an id with exactly one P-NNN-*.md, or a .md inside the
# folder) = file intake; any other token = raw intake (the owner describing an item), the resolved files listed as
# merge targets. Arguments that only say "all" (`all`, `todas as pendências`, `every open item`) = no argument.
set -u

fail() { echo "INTAKE FAILED: $*"; exit 1; }
usage() { echo "INTAKE FAILED: usage: intake.sh <root> [--dir <folder>] [<P-NNN | path.md | text>…] | intake.sh <root> [--dir <folder>] --next"; exit 2; }

[ $# -ge 1 ] || usage
[ -d "$1" ] || usage
root=$(cd "$1" && pwd -P) || usage
shift

if [ "${1:-}" = --dir ]; then
  [ $# -ge 2 ] || usage
  case $2 in /*) dir=$2 ;; *) dir=$root/$2 ;; esac
  [ -d "$dir" ] || fail "no folder $dir (--dir)"
  dir=$(cd "$dir" && pwd -P) || fail "cannot enter $dir"
  shift 2
else
  dir=$root/pending
  mkdir -p "$dir" || fail "cannot create $dir"
  git -C "$root" check-ignore -q pending 2>/dev/null
  if [ $? -eq 1 ]; then
    exclude=$(git -C "$root" rev-parse --git-path info/exclude 2>/dev/null) && {
      case $exclude in /*) ;; *) exclude=$root/$exclude ;; esac
      mkdir -p "$(dirname "$exclude")" && echo '/pending/' >> "$exclude"
    }
  fi
fi

if [ $# -eq 1 ] && [ "$1" = --next ]; then
  high=0
  for f in "$dir"/P-[0-9][0-9][0-9]*.md "$dir"/done/P-[0-9][0-9][0-9]*.md; do
    [ -e "$f" ] || continue
    n=${f##*/P-}; n=${n:0:3}
    [ $((10#$n)) -gt "$high" ] && high=$((10#$n))
  done
  # Every pending file git ever saw counts too (a folder that was tracked before it became local), so an id
  # is never reused. Outside a git work tree, or with git failing or absent, only the folder counts.
  while IFS= read -r p; do
    p=${p##*/}
    [[ $p == P-[0-9][0-9][0-9]*.md ]] || continue
    n=${p:2:3}
    [ $((10#$n)) -gt "$high" ] && high=$((10#$n))
  done < <(git -C "$root" log --all --diff-filter=A --name-only --format= -- ':(glob)**/P-[0-9][0-9][0-9]*.md' 2>/dev/null)
  printf 'P-%03d\n' $((high + 1))
  exit 0
fi

# The owner asking for everything in words: an "all" word, alone or with filler words, is the no-argument call.
if [ $# -gt 0 ]; then
  all=0; other=0
  for tok in "$@"; do
    word=${tok,,}
    while [[ $word == *[,\;:.!?\)] ]]; do word=${word%?}; done; word=${word#(}
    case $word in
      all|every|everything|todas|todos|tudo) all=1 ;;
      the|open|pending|item|items|file|files|as|os|pendências|pendencias|pendentes|abertas|abertos|itens|arquivos) ;;
      *) other=1 ;;
    esac
  done
  if [ "$all" = 1 ] && [ "$other" = 0 ]; then set --; fi
fi

found=()
intake='file'
if [ $# -eq 0 ]; then
  for f in "$dir"/P-*.md; do
    [ -f "$f" ] || continue
    head -n 10 "$f" | grep -qE '^status:[[:space:]]*open[[:space:]]*$' && found+=("$f")
  done
  [ ${#found[@]} -gt 0 ] || fail "no open pending file in $dir"
else
  for tok in "$@"; do
    hit=
    while [[ $tok == *[,\;:.!?\)] ]]; do tok=${tok%?}; done; tok=${tok#(}
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
