# Retros e relatório do `/wh:implementation`

## Retro (cada faixa e o orquestrador)

`Skill(wh:retro, "arquivo: <caminho>")` sobre a própria sessão, de memória (sem reler logs grandes). O passo "apresentar ao usuário" da skill vira o arquivo `<raiz>/.impl/<slug>/retros/<faixa|orquestrador>.md` (≤ 40 linhas, ≤ 6 candidatos); nenhuma proposta é aplicada. Agente em worktree: o arquivo sai pelo Bash com heredoc (`AMBIENTE.md` § Arquivos fora da worktree).

```markdown
# Retro · <faixa> · <data>
| # | Severidade | Categoria | Evidência (o que aconteceu, comando/arquivo) | Proposta (arquivo e mudança) | Quem aplica (repo / dono, fora do repo) |
```

## Relatório (perfil § Relatório, padrão `docs/relatorios/<data>-<slug>.md`, só o orquestrador)

Fontes: os relatórios das faixas, o quadro (`HUMANO`, `AVISO`, `FIM` com o estado de cada faixa), as retros, a validação da fase 4, os conflitos de merge que você resolveu e os relatórios do QA (`qa/<faixa|codigo>.md`, `qa/final.md` e os retestes). Cada linha diz o quê, onde (arquivo/símbolo ou comando) e o que já está pronto; ação do dono com o comando ou texto pronto.

```markdown
# <título> · <data> · impl/<slug> · <PR pelo GitHub | sem PR>
Pedido enriquecido (3 linhas). Faixas: <faixa: itens, commits>. Sem PR: o comando de merge da fase 6.5.

## Erros
Falhas de teste, check ou lint que sobraram, conflitos de merge e como foram resolvidos, consertos feitos na integração.

## Pendências
Itens pulados ou parciais e por quê; linhas HUMANO; decisões tomadas sem o dono (pergunta, opção adotada, alternativa) e linhas `[inferido]` do perfil sem confirmar; contratos que mudaram (campos) e o que precisa de deploy conjunto; cenários para o QA visual/e2e do perfil; seções do perfil que ficaram `—` e a fase que isso pulou.

## QA
Decisões contestadas pelo QA de código (decisão, objeção, o que ficou); achados do QA de código e do QA visual/e2e: corrigidos (commit) / retestados / registrados (por quê). Revisão mais funda, só se o dono quiser e só com PR: `/code-review ultra <n do PR>` (multiagente na nuvem, cobrado). O número do PR nasce na fase 6.5, depois deste arquivo: o comando pronto vai na resposta final. Sem PR, esta seção não cita o `ultra`. Nenhum agente nem subagente dispara o `ultra` nem o propõe como próximo passo de agente.

## Problemas encontrados
Achados fora do escopo (bugs, dívidas vizinhas), cada um com evidência.

## Retro consolidada
| # | Severidade | Categoria | Evidência (faixas) | Proposta | Quem aplica |
Candidatos de todas as retros, deduplicados (o mesmo problema em várias faixas = uma linha citando todas), por severidade.
```

O relatório só registra: as correções ficam para o dono, menos a linha de perfil que a fase 6.2 do `SKILL.md` manda aplicar.
