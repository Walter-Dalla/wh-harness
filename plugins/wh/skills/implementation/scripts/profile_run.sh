#!/usr/bin/env bash
# Runs one key of the `## Commands` section of the implementation profile, so the verdict is the command's own
# exit and never the exit of a filter piped after it.
#
#   profile_run.sh <key> [<worktree>=.] [--port <p>] [--slug <s>] [--log <file>] [--print]
#
# <key>: build, suite, typecheck, service or health. Reads <worktree>/.claude/profile/implementation.md, section
# `## Commands` (up to the next `## ` heading), the line `<key>: ` followed by a command in backticks or `—`.
# `<port>` and `<slug>` in the command are replaced by --port and --slug.
# Run: `bash -c <command>` in <worktree>, stdout and stderr to the log (--log, else a temporary file removed at
# the end); then the last 30 lines of the log and, as the last line, `PROFILE_RUN <key>: exit <n>`; exits <n>.
# `—`: prints `PROFILE_RUN <key>: skipped`, exit 0. --print: prints only the command (or `—`), exit 0.
# Exit 2 with `PROFILE_RUN FAILED: <reason>`: bad call, unknown key, profile or section missing, key line missing
# or malformed, `<port>`/`<slug>` left in the command.
set -u

fail() { echo "PROFILE_RUN FAILED: $*"; exit 2; }
usage() { fail "usage: profile_run.sh <build|suite|typecheck|service|health> [<worktree>] [--port <p>] [--slug <s>] [--log <file>] [--print]"; }

[ $# -ge 1 ] || usage
key=$1; shift
case $key in
  build|suite|typecheck|service|health) ;;
  *) fail "unknown key '$key' (build, suite, typecheck, service, health)" ;;
esac

wt=; port=; slug=; log=; print=0
while [ $# -gt 0 ]; do
  case $1 in
    --port|--slug|--log)
      [ $# -ge 2 ] && [ -n "$2" ] || fail "$1 without a value"
      case $1 in --port) port=$2 ;; --slug) slug=$2 ;; --log) log=$2 ;; esac
      shift 2 ;;
    --print) print=1; shift ;;
    -*) fail "unknown option $1" ;;
    *) [ -z "$wt" ] || fail "more than one worktree: $wt, $1"; wt=$1; shift ;;
  esac
done
[ -n "$wt" ] || wt=.
[ -d "$wt" ] || fail "worktree $wt is not a folder"

profile=$wt/.claude/profile/implementation.md
[ -f "$profile" ] || fail "profile $profile missing"
grep -qE '^## Commands[[:space:]]*$' "$profile" || fail "no ## Commands section in $profile (/wh:profile implementation)"

line=$(awk -v key="$key" '/^## /{ if (insec) exit; insec = ($0 ~ /^## Commands[[:space:]]*$/); next }
  insec && index($0, key ":") == 1 { print; exit }' "$profile")
[ -n "$line" ] || fail "no '$key:' line in the ## Commands section of $profile"

tick='^'"$key"':[[:space:]]+`([^`]+)`'
dash='^'"$key"':[[:space:]]+—'
if [[ $line =~ $tick ]]; then
  cmd=${BASH_REMATCH[1]}
elif [[ $line =~ $dash ]]; then
  cmd=—
else
  fail "malformed '$key:' line (a command in backticks or —): $line"
fi

if [ "$cmd" != — ]; then
  if [[ $cmd == *'<port>'* ]]; then
    [ -n "$port" ] || fail "'$key' needs --port (the command has <port>)"
    cmd=${cmd//<port>/$port}
  fi
  if [[ $cmd == *'<slug>'* ]]; then
    [ -n "$slug" ] || fail "'$key' needs --slug (the command has <slug>)"
    cmd=${cmd//<slug>/$slug}
  fi
fi

if [ "$print" = 1 ]; then
  printf '%s\n' "$cmd"
  exit 0
fi
if [ "$cmd" = — ]; then
  echo "PROFILE_RUN $key: skipped"
  exit 0
fi

if [ -z "$log" ]; then
  log=$(mktemp) || fail "cannot create a temporary log"
  trap 'rm -f "$log"' EXIT
fi
(cd "$wt" && bash -c "$cmd") > "$log" 2>&1
code=$?
tail -n 30 "$log"
echo "PROFILE_RUN $key: exit $code"
exit "$code"
