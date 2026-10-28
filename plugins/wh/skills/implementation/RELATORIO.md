# Retros e relatório do `/wh:implementation`

## Retro (cada faixa e o orquestrador)

Siga a skill de retro do usuário em `~/.claude/skills/retro/SKILL.md`, se existir; sem ela, procure candidatos nestas categorias: navegação, checagem automática, padrão de código, steering doc, economia de ferramenta, no-op, acesso a informação, sobre a própria sessão, de memória (sem reler logs grandes). O passo "apresentar ao usuário" vira o arquivo `<raiz>/.impl/<slug>/retros/<faixa|orquestrador>.md` (≤ 40 linhas, ≤ 6 candidatos); nenhuma proposta é aplicada.

```markdown
# Retro · <faixa> · <data>
| # | Severidade | Categoria (navegação, checagem automática, padrão de código, steering doc, economia de ferramenta, no-op, acesso a informação) | Evidência (o que aconteceu, comando/arquivo) | Proposta (arquivo e mudança) | Quem aplica (repo / dono, fora do repo) |
```

## Relatório (perfil § Relatório, padrão `docs/relatorios/<data>-<slug>.md`, só o orquestrador)

Fontes: os relatórios das faixas, o quadro (`HUMANO`, `AVISO`, `FIM` com o estado de cada faixa), as retros, a validação da fase 4, os conflitos de merge que você resolveu e os relatórios do QA (`qa/<faixa|codigo>.md`, `qa/final.md` e os retestes). Cada linha diz o quê, onde (arquivo/símbolo ou comando) e o que já está pronto; ação do dono com o comando ou texto pronto.

```markdown
# <título> · <data> · PR #<n>
Pedido enriquecido (3 linhas). Faixas: <faixa: itens, commits>.

## Erros
Falhas de teste, check ou lint que sobraram, conflitos de merge e como foram resolvidos, consertos feitos na integração.

## Pendências
Itens pulados ou parciais e por quê; linhas HUMANO; contratos que mudaram (campos) e o que precisa de deploy conjunto; cenários para o QA visual/e2e do perfil; seções do perfil que ficaram `—` e a fase que isso pulou.

## QA
Decisões contestadas pelo QA de código (decisão, objeção, o que ficou); achados do QA de código e do QA visual/e2e: corrigidos (commit) / retestados / registrados (por quê). Revisão mais funda, só se o dono quiser: `/code-review ultra <n do PR>` (multiagente na nuvem, cobrado). Nenhum agente nem subagente dispara o `ultra`; o relatório e a resposta dão o comando pronto para o dono colar, nunca o propõem como próximo passo de agente.

## Problemas encontrados
Achados fora do escopo (bugs, dívidas vizinhas), cada um com evidência.

## Retro consolidada
| # | Severidade | Categoria | Evidência (faixas) | Proposta | Quem aplica |
Candidatos de todas as retros, deduplicados (o mesmo problema em várias faixas = uma linha citando todas), por severidade.
```

O relatório só registra: as correções ficam para o dono.
