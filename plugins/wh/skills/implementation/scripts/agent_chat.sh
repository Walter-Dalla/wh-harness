#!/usr/bin/env bash
# Persists one agent consultation per file in <impl>/agent_chat/ (question, then the answers), with UTC timestamps.
#
#   agent_chat.sh <impl> ask <lane> <item> <who> <text…>        creates <impl>/agent_chat/NN-<lane>-<item>.md
#   agent_chat.sh <file> answer <who> <impact> <text…>          appends an answer to <file>
#
# Prints the absolute path of the file only. NN = files already in agent_chat/ + 1, two digits. <impact> is free
# text (item, lane, other lanes: x, contract, replan). One simple command, no `$(…)` on the caller's side.
set -u

usage() {
  echo "AGENT_CHAT FAILED: usage: agent_chat.sh <impl> ask <lane> <item> <who> <text…> | <file> answer <who> <impact> <text…>"
  exit 2
}
fail() { echo "AGENT_CHAT FAILED: $*"; exit 1; }

[ $# -ge 2 ] || usage
now=$(date -u +%FT%TZ)
case $2 in
  ask)
    [ $# -ge 6 ] || usage
    impl=$1; lane=$3; item=$4; who=$5; shift 5
    chat=$impl/agent_chat
    [ -d "$chat" ] || fail "$chat does not exist (the orchestrator creates it in phase 1)"
    chat=$(cd "$chat" && pwd -P) || fail "cannot enter $chat"
    n=0
    for f in "$chat"/*; do [ -f "$f" ] && n=$((n + 1)); done
    nn=$(printf '%02d' $((n + 1)))
    file=$chat/$nn-$lane-$item.md
    [ -e "$file" ] && fail "$file already exists"
    printf '# Chat %s · %s %s · %s\n\n## Question (%s)\n\n%s\n' "$nn" "$lane" "$item" "$now" "$who" "$*" > "$file" \
      || fail "cannot write $file"
    echo "$file"
    ;;
  answer)
    [ $# -ge 5 ] || usage
    file=$1; who=$3; impact=$4; shift 4
    [ -f "$file" ] || fail "$file does not exist"
    printf '\n## Answer (%s) · impact: %s · %s\n\n%s\n' "$who" "$impact" "$now" "$*" >> "$file" \
      || fail "cannot write $file"
    echo "$(cd "$(dirname "$file")" && pwd -P)/$(basename "$file")"
    ;;
  *) usage ;;
esac
