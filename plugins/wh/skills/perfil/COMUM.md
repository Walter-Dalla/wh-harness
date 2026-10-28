# Modelo de `.claude/perfil/_comum.md`

Fatos que toda skill usa. Cada linha com a fonte entre colchetes. Seção sem resposta: `—`.

```markdown
# Perfil comum

## Clone
Onde a sessão e as worktrees rodam (toolchain nativa) e o que o outro checkout é, se houver. `—` = o checkout atual.

## Toolchain
Os comandos que mudam por checkout ou SO: build/test (`dotnet` vs `dotnet.exe`, `pnpm`…), HTTP local (`curl` vs `curl.exe`), Python, como matar processo. Como alcançar o localhost do outro lado (WSL ↔ Windows).

## Git
Principal: `main`. Remote de PR: `origin` (ou o nome que aponta para o GitHub). Branches protegidas. Identidade e push (ex.: `git -c user.name=…`, `git.exe push` quando a credencial mora no Windows). Checkout compartilhado com outras sessões: `git branch --show-current` antes de commitar.

## Portas
Do dono (nunca usadas por skill): `5000`. Faixa dos agentes do `/wh:implementation`: `5100–5105`. QA visual/e2e: a partir de `5108` (primeira livre, nunca derruba o que já está numa porta).

## Navegação
`.codegraph/` presente e o que cobre: `codegraph explore -p . "<símbolos ou pergunta>"` (worktree: `codegraph init -y .` uma vez; `codegraph sync .` depois de editar). O que o índice não cobre (linguagens, cenas, configs, docs): `grep`/`Read`. Índice do cliente, se houver (ex.: `scripts/INDICE.md`).

## Docs
Um por linha, `caminho` — o que é: mapa (`CLAUDE.md`), regras de camada que não carregam sozinhas (`conventions.md`, `<cliente>/CLAUDE.md`), mapa de features (`docs/features/README.md`), status e dívida (`FEATURES.md`), glossário, pendências do dono e dos agentes, changelog, relatórios de tarefa, brief de UI.

## Limites
O que nenhum agente toca: produção (URL, servidor, SSH), MCPs reais, portas e bancos do dono, arquivos fora do repo e do scratchpad, segredos.
```
