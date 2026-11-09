#!/usr/bin/env bash
# Appends one line to the task board with a fresh UTC timestamp: `<date> | <who> | <KIND> | <text>`.
#
#   board.sh <board> <who> <KIND> <text...>
#
# One simple command, no `$(…)` on the caller's side: made for the agent worktree, where the guard refuses
# substitutions. KIND is uppercased (START, CONTRACT, WARNING, HUMAN, CONSULT, END, MERGE, WAVE).
set -u
if [ $# -lt 4 ]; then
  echo "BOARD FAILED: usage: board.sh <board> <who> <KIND> <text...>"
  exit 2
fi
board=$1; who=$2; kind=$(printf '%s' "$3" | tr '[:lower:]' '[:upper:]'); shift 3
[ -f "$board" ] || { echo "BOARD FAILED: $board does not exist (the orchestrator creates it in phase 1)"; exit 1; }
line="$(date -u +%FT%TZ) | $who | $kind | $*"
printf '%s\n' "$line" >> "$board" || { echo "BOARD FAILED: cannot write $board"; exit 1; }
echo "$line"
