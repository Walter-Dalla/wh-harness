#!/usr/bin/env bash
# Preflight de um subagente do /wh:implementation (impl-dev, impl-qa), ANTES de qualquer
# git reset/branch: confere o ambiente e para sem tocar em nada se algo não bate.
# Uso: preflight.sh --base <hash> [--branch <impl/slug-faixa>] [--port <porta>] [--lane <arquivo da faixa>] [--protected <main,release/*>]
# Saída: "PREFLIGHT OK" (exit 0) ou uma linha "PREFLIGHT FALHOU: …" por problema (exit 1).
set -u
base='' branch='' port='' lane='' protected='main,master,develop'
while [ $# -gt 0 ]; do
  case "$1" in --base|--branch|--port|--lane|--protected)
    [ $# -ge 2 ] || { echo "PREFLIGHT FALHOU: $1 sem valor"; exit 2; } ;;
  esac
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

# Branch: a worktree recém-criada (prefixo do isolation "worktree" do Claude Code, hoje worktree-agent-; WH_AGENT_BRANCH_PREFIX troca) ou a branch da faixa (retomada).
prefix=${WH_AGENT_BRANCH_PREFIX:-worktree-agent-}
cur=$(git branch --show-current)
case "$cur" in
  "$prefix"*) ;;
  '') err "HEAD solto" ;;
  *) [ -n "$branch" ] && [ "$cur" = "$branch" ] || err "branch atual '$cur' não é ${prefix}* nem a esperada '${branch:-<nenhuma>}'" ;;
esac
if [ -n "$branch" ]; then
  IFS=',' read -ra prot <<< "$protected"
  # shellcheck disable=SC2053
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
port_busy() {  # 0 ocupada, 1 livre, 2 sem ferramenta para conferir
  if command -v ss >/dev/null 2>&1; then ss -ltnH "sport = :$1" 2>/dev/null | grep -q .
  elif command -v lsof >/dev/null 2>&1; then lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else return 2; fi
}
if [ -n "$port" ] && [ "$port" != "—" ]; then
  port_busy "$port"; case $? in
    0) err "porta $port ocupada" ;;
    2) echo "PREFLIGHT AVISO: sem ss nem lsof; porta $port não conferida" ;;
  esac
fi

# Arquivo da faixa e o quadro ao lado dele.
if [ -n "$lane" ]; then
  [ -r "$lane" ] || err "arquivo da faixa ilegível: $lane"
  [ -e "$(dirname "$lane")/QUADRO.md" ] || err "quadro ausente: $(dirname "$lane")/QUADRO.md"
fi

# .impl/ (quadro, checkpoint, saídas) fica fora do git: pelo info/exclude do clone (fase 1) ou pelo .gitignore do repo.
git -C "$top" check-ignore -q .impl/preflight 2>/dev/null || err ".impl/ não é ignorado pelo git (fase 1 do /wh:implementation: $common/info/exclude)"

[ $fail -eq 0 ] && echo "PREFLIGHT OK: $top @ $cur, base $base${port:+, porta $port}"
exit $fail
