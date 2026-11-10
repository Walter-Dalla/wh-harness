#!/usr/bin/env bash
# Persists one agent consultation per file in <impl>/agent_chat/ (question, then the answers), with UTC timestamps.
#
#   agent_chat.sh <impl> ask <lane> <item> <who> <text…>        creates <impl>/agent_chat/NN-<lane>-<item>.md
#   agent_chat.sh <file> answer <who> <impact> <text…>          appends an answer to <file>
#
# Prints the absolute path of the file only. NN = highest NN- prefix in agent_chat/ + 1, two digits, chosen under
# the lock agent_chat/.lock (retried every 0.05 s, WH_CHAT_LOCK_TRIES times, default 100), so parallel asks get
# distinct numbers. <impact> is free text (item, lane, other lanes: x, contract, replan). One simple command, no
# `$(…)` on the caller's side.
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
    lock=$chat/.lock
    tries=${WH_CHAT_LOCK_TRIES:-100}
    i=0
    # The lock is a file created with noclobber (bash opens it with O_EXCL): `mkdir` is not atomic in every
    # coreutils (uutils `mkdir` lets two racers both succeed).
    until (set -o noclobber; : > "$lock") 2>/dev/null; do
      [ "$i" -lt "$tries" ] || fail "$lock is held (remove it if no ask is running)"
      i=$((i + 1))
      sleep 0.05
    done
    # Only this process took the lock, so only this process removes it.
    trap 'rm -f "$lock"' EXIT
    n=0
    for f in "$chat"/[0-9][0-9]-*.md; do
      [ -f "$f" ] || continue
      p=${f##*/}; p=$((10#${p:0:2}))
      [ "$p" -gt "$n" ] && n=$p
    done
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
