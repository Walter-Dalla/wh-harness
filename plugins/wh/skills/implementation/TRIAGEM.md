# Triagem e plano do `/wh:implementation`

O enriquecedor aplica na etapa `planejar`; o orquestrador confere.

## Triagem

| Tamanho | Sinal | Execução |
|---|---|---|
| **pequena** | uma camada, ou contrato com consumidor pequeno; ≤ ~8 arquivos | o orquestrador, inline (fase 3 do `SKILL.md`) |
| **grande** | várias camadas unidas por contrato, > ~8 arquivos, ou blocos independentes que andam em paralelo | faixas `impl-dev` (`FAIXAS.md` §1) |

Além do tamanho, o **risco**: contrato usado por vários consumidores, formato persistido, caminho crítico do produto ou concorrência pesam para grande mesmo com poucos arquivos, porque ganham faixa própria, QA por faixa e o consumidor em onda separada. Paralelizar só compensa com blocos realmente independentes; sem eles, uma faixa ou inline. Na dúvida entre as duas com risco baixo, pequena: inline é mais barato.

## Plano

`<raiz>/.impl/<slug>/PLANO.md`:

```markdown
# <título> · <data>
Pedido: <o do dono, uma linha>. Enriquecido: <o que ele quer dizer no produto e no código, 3–5 linhas>. Análise: ANALISE.md.
Decisões: <respostas do dono e as do enriquecedor, com o porquê; "(sem dono)" na que o orquestrador adotou sem perguntar>.
| Id | Item | Arquivos (símbolo) | Tipo (interno/contrato) | Aceite (comando) |
```

Id = `<slug>-N`, em ordem de dependência: produtor do contrato antes do consumidor, refactor antes da feature que mexe no mesmo código, correção de bug e refactor em itens separados. Tipo **contrato** = muda uma interface entre partes (API, DTO, evento, formato persistido, CLI); o resto é **interno**. Aceite = um comando que fica verde só com o item feito; item de refactor (comportamento igual): a suíte da área, verde antes e depois. Grande: mais a tabela de ondas do `FAIXAS.md` §1.
