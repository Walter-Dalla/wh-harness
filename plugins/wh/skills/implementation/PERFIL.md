# Perfil do `/wh:implementation`: `.claude/perfil/implementation.md`

O que o `/wh:implementation` e os agentes `impl-*` precisam saber do repositório. A skill e os agentes citam seções (`perfil § Testes`), nunca comandos. Clone, toolchain, git, portas, navegação, docs e limites moram no `.claude/perfil/_comum.md` (modelo: `${CLAUDE_PLUGIN_ROOT}/skills/perfil/COMUM.md`); aqui só o que é desta skill. Gerado e completado pela skill `perfil` (`Skill(wh:perfil, "implementation")`): fontes em ordem, uma linha por fato com a fonte entre colchetes, `—` na seção sem resposta (a fase que depende dela é pulada e o relatório diz que foi).

## Modelo

```markdown
# Perfil do /wh:implementation

## Build
`<comando>` (sem warning novo = verde). Saída filtrada: `… 2>&1 | tail -30`.

## Testes
Área: `<comando com <filtro>>` (ex.: `dotnet test X --filter "FullyQualifiedName~<filtro>"`, `npm test -- <filtro>`, `pytest -k <filtro>`).
Suíte: `<comando completo> 2>&1 | grep -E "<padrão de passou/falhou>"`.
Aceite de item = o teste de área que só fica verde com o item feito; teste novo quando não há. Relógio e aleatoriedade injetados onde o repo injeta.

## Checks
Lint/typecheck/formatação/verificação de cliente, um por linha, com o comando e quando roda (por item, fim de faixa, QA final). Ex.: `deploy/lint.sh` (QA final, sem `--update`).

## Serviço descartável
Como subir uma instância isolada para testar (API, servidor, banco), com `<porta>` e `<slug>` no comando, o health check e como parar. Fixtures de estado, se houver. Portas: `_comum § Portas`. `—` = o repo não precisa de serviço.

## Contrato
O que conta como contrato (API pública, DTO, evento, formato persistido, CLI, schema) e como a fixture de contrato é atualizada e revisada (snapshot: variável de aceite e o `git diff` da pasta; golden file; schema gerado). Testes do produtor e do consumidor.

## Arquivos de união
Arquivos que várias faixas acrescentam linhas (constantes, mensagens, traduções, códigos de erro, registro de DI): só acréscimo; o orquestrador resolve no merge. Entre crases: `<glob>` `<glob>`.

## Arquivos protegidos
O que só o orquestrador edita (changelog, docs de feature, convenções, `CLAUDE.md`, perfis, relatórios).

## Leitura do enriquecedor
Quais docs do `_comum § Docs` a análise lê sempre, quais só quando a tarefa toca a área, e os índices de código a ler antes de qualquer grep.

## QA visual ou e2e
Skill ou comando que exercita o produto de ponta a ponta (ex.: `/wh:qa-visual <áreas> --autonomo`, `npx playwright test`), o que ele precisa (serviço na porta do QA final, libs) e onde escreve o relatório. `—` = pula.

## Docs de fim
Onde entra o que a tarefa muda ou deixa aberto: changelog, status de features, pendências do dono, convenções, glossário, mapa de features (skill), limpeza (skill). `—` para cada um que não existe.

## Relatório
Pasta dos relatórios de tarefa (padrão `docs/relatorios/<data>-<slug>.md`).

## Modelos
Regra do dono para modelo e esforço por papel (enriquecedor, faixa mecânica, faixa estrutural, QA). `—` = padrão da skill.

## Comandos na worktree
Aprendido pelas execuções: o que o guard de isolamento recusa e a forma que passa. `—` no primeiro perfil; as retros acrescentam.
```
