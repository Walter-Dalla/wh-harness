---
name: limpeza
description: Limpa os .md do repositório depois de uma execução — apaga planos, prompts e faixas executados, leva o que ficou aberto (dívida, pendência do dono, convenção, termo) para a casa certa e atualiza os .md que citam código que mudou; no fim commita e remove as worktrees locais. Use no fim do /wh:implementation, no fim de um plano ou quando pedirem "limpar os docs", "limpeza". Casas, permanentes e poda vêm de .claude/perfil/limpeza.md.
---

# Limpeza dos `.md`

Perfil do projeto (injetado; `PERFIL_AUSENTE` = `Skill(wh:perfil, "limpeza")` antes de seguir):
!`cat .claude/perfil/_comum.md .claude/perfil/limpeza.md 2>/dev/null || echo PERFIL_AUSENTE`

Entrada: um `slug` do `/wh:implementation` (escopo = `<principal>...impl/<slug>` e a pasta de plano do perfil § Consumidos), ou uma lista de arquivos/pastas de plano e um intervalo de commits. Você trabalha na branch da execução; tudo vira um commit no formato do perfil § Commit.

Cada **achado aberto tem uma casa**, e só uma: a tabela do perfil § Casas.

## 1. Inventário

- **Consumidos:** os `.md` que a execução leu como instrução (perfil § Consumidos: plano e faixas, prompts, dívidas, prompt citado no pedido). Para cada um: executado inteiro, em parte, ou não tocado (pelos ids nos commits: `git log <principal>..HEAD --format=%s`).
- **Afetados:** `git diff <principal>...HEAD --name-status` e os símbolos, arquivos, rotas, constantes e chaves que o diff criou, renomeou ou apagou. Cada nome velho e cada caminho apagado, procurado nos `.md` do repo: `git grep -n -e '<nome>' -- '*.md'`.

**Feito quando todo `.md` consumido tem estado e todo nome/caminho mudado tem a lista de `.md` que o citam.**

## 2. Salvar o que está aberto

Em cada `.md` consumido, o que **não** foi executado ou ficou como achado (item pulado, parcial, `HUMANO`, decisão para depois, "fora do escopo") vai para a casa do perfil § Casas, com a evidência em uma linha, se a casa ainda não o tem. Linha de status ou pendência que a execução resolveu (confira no código) sai.

**Feito quando todo item aberto dos consumidos está numa casa e nenhuma casa lista algo já resolvido por esta execução.**

## 3. Apagar o executado

- Executado inteiro: `git rm` (ou `rm -r` fora do git, como a pasta de plano depois que o relatório existe). Em parte: só os itens feitos saem; o arquivo fica com o resto.
- Pasta vazia sai; índice que apontava para o arquivo (README, `CLAUDE.md`, "sob demanda") perde a linha.
- Poda do changelog pela regra do perfil § Poda.
- Fica sempre: a lista do perfil § Permanentes.

**Feito quando nenhum `.md` executado inteiro existe e nenhum item feito sobra num `.md` parcial.**

## 4. Atualizar o que mudou

Para cada `.md` afetado do passo 1: nome velho pelo novo, o apagado sai, a regra que o diff mudou ajustada conferindo no código (`_comum § Navegação`), nunca pelo relatório. Mapa de features pela skill do perfil § Casas. Comentário em código que cita `.md` apagado: aponte para o commit (`git show <hash>:<arquivo>`).

**Feito quando `git grep` de cada nome velho e de cada caminho apagado não acha nada fora do changelog, do relatório e do histórico.**

## 5. Commit

`git add -A` dos `.md` tocados; commit no formato do perfil § Commit, com a lista de apagados e de achados movidos (casa → item) no corpo.

## 6. Worktrees

Cada worktree de `git worktree list --porcelain`, menos o checkout principal e a worktree onde você está:

- **Mudança não commitada** (`git -C <wt> status --porcelain` com saída): `git -C <wt> add -A`. Conteúdo já salvo quando `git -C <wt> diff --cached --quiet <ref> -- <arquivos do status>` passa para `<principal>` ou para `origin/<branch>`; aí a worktree segue direto para remoção. Senão, commit na branch da worktree no formato do perfil § Commit (detached HEAD: `git -C <wt> switch -c wt/<pasta>` antes).
- **Remoção:** `git worktree remove <wt>`; `--force` só para mudança já salva em `<principal>` ou `origin/<branch>`; travada, `git worktree unlock <wt>` antes. A branch fica. No fim, `git worktree prune`.

**Feito quando `git worktree list` mostra só o checkout principal e a worktree atual, e toda mudança das removidas está num commit, em `<principal>` ou em `origin/<branch>`.**

Resposta (≤ 8 linhas): apagados, parciais, achados movidos, `.md` atualizados, worktrees removidas (branch e commit novo, se houve).
