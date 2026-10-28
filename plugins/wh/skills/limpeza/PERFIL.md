# Perfil do `/wh:limpeza`: `.claude/perfil/limpeza.md`

Gerado pela skill `perfil`. Uma linha por fato, fonte entre colchetes, `—` na seção sem resposta.

```markdown
# Perfil do /wh:limpeza

## Casas
Tabela "achado aberto → casa", uma linha por tipo: dívida técnica ou item por fazer; ação do dono no servidor/máquina; decisão aberta do dono; decisão tomada, ideia, medição; regra de código nova (doc de convenções por camada); conceito novo ou nome trocado (glossário); regra ou fluxo de feature (skill `/wh:feature-docs`); erro, pendência e retro da execução (o relatório, já escrito).

## Consumidos
Onde vivem os `.md` que uma execução lê como instrução: pasta de plano (`.impl/<slug>/`), prompts (`todo_prompts/`), dívidas (`docs/dividas/**`), outros.

## Permanentes
Arquivos e pastas que a limpeza nunca apaga (changelog, status, mapa de features, glossário, pendências, relatórios, convenções, `CLAUDE.md`, `.claude/**`, baselines de lint).

## Poda
Regra de poda do changelog: idade (dias) que vira linha resumida com `git show <hash>:CHANGELOG.md`, tamanho máximo (KB) e como avança. `—` = sem poda.

## Relatório
Pasta dos relatórios de execução (`docs/relatorios/<data>-<slug>.md`): o que já está neles não se duplica.

## Commit
Formato da mensagem (`Docs: limpeza <slug>`) e identidade/push, se diferem do `_comum § Git`.
```
