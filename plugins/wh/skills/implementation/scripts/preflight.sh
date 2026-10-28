#!/usr/bin/env bash
# Preflight de um subagente do /wh:implementation (impl-dev, impl-qa), ANTES de qualquer
# git reset/branch: confere o ambiente e para sem tocar em nada se algo não bate.
# Uso: preflight.sh --base <hash> [--branch <impl/slug-faixa>] [--port <porta>] [--lane <arquivo da faixa>] [--protected <main,release/*>]
# Saída: "PREFLIGHT OK" (exit 0) ou uma linha "PREFLIGHT FALHOU: …" por problema (exit 1).
set -u
base='' branch='' port='' lane='' protected='main,master,develop'
while [ $# -gt 0 ]; do
  case "$1" in
    --base) base=$2; shift 2 ;;
    --branch) branch=$2; shift 2 ;;
    --port) port=$2; shift 2 ;;
    --lane) lane=$2; shift 2 ;;
    --protected) protected="$protected,$2"; shift 2 ;;
    *) echo "PREFLIGHT FALHOU: argumento desconhecido: $1"; exit 2 ;;
  esac
done

fail=0
err() { echo "PREFLIGHT FALHOU: $*"; fail=1; }

top=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "PREFLIGHT FALHOU: fora de um repositório git"; exit 1; }
gitdir=$(cd "$top" && git rev-parse --absolute-git-dir)
common=$(cd "$top" && git rev-parse --path-format=absolute --git-common-dir)

# Worktree de agente: nunca o checkout principal.
[ "$gitdir" != "$common" ] || err "não é uma worktree de agente: $top é o checkout principal"

# Branch: a worktree recém-criada (worktree-agent-*) ou a branch da faixa (retomada).
cur=$(git branch --show-current)
case "$cur" in
  worktree-agent-*) ;;
  '') err "HEAD solto" ;;
  *) [ -n "$branch" ] && [ "$cur" = "$branch" ] || err "branch atual '$cur' não é worktree-agent-* nem a esperada '${branch:-<nenhuma>}'" ;;
esac
if [ -n "$branch" ]; then
  IFS=',' read -ra prot <<< "$protected"
  for p in "${prot[@]}"; do [[ $branch == $p ]] && err "branch esperada protegida: $branch"; done
fi

# Nada local que não pertença à tarefa (o reset --hard apagaria).
dirty=$(git status --porcelain --untracked-files=normal)
[ -z "$dirty" ] || err "alterações locais na worktree (o reset as apagaria): $(echo "$dirty" | head -5 | tr '\n' ' ')"

# Base existe; numa retomada, a ponta atual já contém a base.
if [ -z "$base" ]; then err "--base ausente"
elif ! git cat-file -e "$base^{commit}" 2>/dev/null; then err "base $base não existe no repositório"
fi

# Porta livre (serviço descartável da faixa ou do QA final).
if [ -n "$port" ] && [ "$port" != "—" ]; then
  if ss -ltnH "sport = :$port" 2>/dev/null | grep -q .; then err "porta $port ocupada"; fi
fi

# Arquivo da faixa e o quadro ao lado dele.
if [ -n "$lane" ]; then
  [ -r "$lane" ] || err "arquivo da faixa ilegível: $lane"
  [ -e "$(dirname "$lane")/QUADRO.md" ] || err "quadro ausente: $(dirname "$lane")/QUADRO.md"
fi

# PROGRESS.md fica fora do git em toda worktree.
grep -qx 'PROGRESS.md' "$common/info/exclude" 2>/dev/null || err "PROGRESS.md não está em $common/info/exclude (fase 1 do /wh:implementation)"

[ $fail -eq 0 ] && echo "PREFLIGHT OK: $top @ $cur, base $base${port:+, porta $port}"
exit $fail
