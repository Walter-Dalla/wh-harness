#!/usr/bin/env bash
# Preflight of a /wh:implementation subagent (impl-dev, impl-qa), BEFORE any
# git reset/branch: checks the environment and stops without touching anything if something is off.
# Usage: preflight.sh --base <hash> [--branch <impl/slug-lane>] [--port <port>] [--lane <lane file>] [--protected <main,release/*>]
# Output: "PREFLIGHT OK" (exit 0) or one "PREFLIGHT FAILED: …" line per problem (exit 1).
set -u
base='' branch='' port='' lane='' protected='main,master,develop'
while [ $# -gt 0 ]; do
  case "$1" in --base|--branch|--port|--lane|--protected)
    [ $# -ge 2 ] || { echo "PREFLIGHT FAILED: $1 without a value"; exit 2; } ;;
  esac
  case "$1" in
    --base) base=$2; shift 2 ;;
    --branch) branch=$2; shift 2 ;;
    --port) port=$2; shift 2 ;;
    --lane) lane=$2; shift 2 ;;
    --protected) protected="$protected,$2"; shift 2 ;;
    *) echo "PREFLIGHT FAILED: unknown argument: $1"; exit 2 ;;
  esac
done

fail=0
err() { echo "PREFLIGHT FAILED: $*"; fail=1; }

top=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "PREFLIGHT FAILED: outside a git repository"; exit 1; }
gitdir=$(cd "$top" && git rev-parse --absolute-git-dir)
common=$(cd "$top" && git rev-parse --path-format=absolute --git-common-dir)

# Agent worktree: never the main checkout.
[ "$gitdir" != "$common" ] || err "not an agent worktree: $top is the main checkout"

# Branch: the freshly created worktree (prefix of Claude Code's "worktree" isolation, today worktree-agent-; WH_AGENT_BRANCH_PREFIX overrides) or the lane branch (resumption).
prefix=${WH_AGENT_BRANCH_PREFIX:-worktree-agent-}
cur=$(git branch --show-current)
case "$cur" in
  "$prefix"*) ;;
  '') err "detached HEAD" ;;
  *) [ -n "$branch" ] && [ "$cur" = "$branch" ] || err "current branch '$cur' is not ${prefix}* nor the expected '${branch:-<none>}'" ;;
esac
if [ -n "$branch" ]; then
  IFS=',' read -ra prot <<< "$protected"
  # shellcheck disable=SC2053
  for p in "${prot[@]}"; do [[ $branch == $p ]] && err "expected branch is protected: $branch"; done
fi

# Nothing local that does not belong to the task (the reset --hard would delete it).
dirty=$(git status --porcelain --untracked-files=normal)
[ -z "$dirty" ] || err "local changes in the worktree (the reset would delete them): $(echo "$dirty" | head -5 | tr '\n' ' ')"

# The base exists; on a resumption, the current tip already contains the base.
if [ -z "$base" ]; then err "--base missing"
elif ! git cat-file -e "$base^{commit}" 2>/dev/null; then err "base $base does not exist in the repository"
fi

# Free port (disposable service of the lane or of the final QA).
port_busy() {  # 0 busy, 1 free, 2 no tool to check
  if command -v ss >/dev/null 2>&1; then ss -ltnH "sport = :$1" 2>/dev/null | grep -q .
  elif command -v lsof >/dev/null 2>&1; then lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else return 2; fi
}
if [ -n "$port" ] && [ "$port" != "—" ]; then
  port_busy "$port"; case $? in
    0) err "port $port busy" ;;
    2) echo "PREFLIGHT WARNING: neither ss nor lsof; port $port not checked" ;;
  esac
fi

# Lane file and the board beside it.
if [ -n "$lane" ]; then
  [ -r "$lane" ] || err "lane file unreadable: $lane"
  [ -e "$(dirname "$lane")/BOARD.md" ] || err "board missing: $(dirname "$lane")/BOARD.md"
fi

# .impl/ (board, checkpoint, outputs) stays outside git: through the clone's info/exclude (phase 1) or the repo's .gitignore.
git -C "$top" check-ignore -q .impl/preflight 2>/dev/null || err ".impl/ is not ignored by git (phase 1 of /wh:implementation: $common/info/exclude)"

[ $fail -eq 0 ] && echo "PREFLIGHT OK: $top @ $cur, base $base${port:+, port $port}"
exit $fail
