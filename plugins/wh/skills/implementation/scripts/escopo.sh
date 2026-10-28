#!/usr/bin/env bash
# Confere que uma faixa do /wh:implementation só mudou os arquivos de que é dona.
# Uso: escopo.sh <arquivo da faixa> <base> [<ref>=HEAD]
# Lê do arquivo da faixa as linhas "Dono de:", "Pode tocar" e "União:" (caminhos ou globs entre crases; `*` cruza pastas).
# "União:" são os arquivos de união do perfil (§ Arquivos de união), que toda faixa pode acrescentar.
# Saída: uma linha por arquivo fora do escopo ("FORA: …", exit 1) e os de "Pode tocar" ("AVISO esperado: …").
set -u
lane=${1:?arquivo da faixa}; base=${2:?base}; ref=${3:-HEAD}
[ -r "$lane" ] || { echo "ESCOPO FALHOU: arquivo da faixa ilegível: $lane"; exit 2; }

globs() { grep -E "$1" "$lane" | grep -o '`[^`]*`' | tr -d '`'; }
mapfile -t own < <(globs '^Dono de:')
mapfile -t may < <(globs 'Pode tocar')
mapfile -t union < <(globs 'União:')
[ ${#own[@]} -gt 0 ] || { echo "ESCOPO FALHOU: nenhum caminho entre crases na linha 'Dono de:' de $lane"; exit 2; }

matches() { local f=$1; shift; local g; for g in "$@"; do [[ $f == $g ]] && return 0; done; return 1; }

out=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  if matches "$f" "${own[@]}"; then continue
  elif [ ${#union[@]} -gt 0 ] && matches "$f" "${union[@]}"; then continue
  elif [ ${#may[@]} -gt 0 ] && matches "$f" "${may[@]}"; then echo "AVISO esperado: $f"
  else echo "FORA: $f"; out=1
  fi
done < <(git diff --name-only "$base...$ref")

[ $out -eq 0 ] && echo "ESCOPO OK: $(git diff --name-only "$base...$ref" | wc -l) arquivos dentro da faixa"
exit $out
