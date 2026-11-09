# Test-drive 2 · calculadora, tarefa grande · 2026-11-06

Segunda execução de ponta a ponta do `/wh:implementation`, agora no plugin `wh` 0.6.0 (working tree não commitado, Claude Code 2.1.319), para cobrir o que o test-drive de 2026-10-28 não exercitou: faixas `impl-dev` em worktree, `QUADRO.md`, `progress/`, `escopo.sh`, consultas, QA de código por faixa. Um run headless (`run.sh 3 … --permission-mode bypassPermissions --dangerously-skip-permissions --model opus`) em `/home/walter/calc-harness-test`, a partir de `main` (f846fe2), remote bare local, sem dono.

Pedido: parser de expressões (precedência, parênteses, menos unário), histórico em arquivo JSON com subcomando `history`, CLI aceitando a expressão inteira, testes; com "Triagem: grande" no pedido, para forçar faixas.

Logs (fora do git): `/home/walter/calc-harness-logs/run-3/` (`session.jsonl`, `events.jsonl`, `impl-snapshot/`, `git/`, `analysis.txt`). Relatório que o harness escreveu: `calc-harness-test/docs/relatorios/2026-11-06-expr-hist.md`.

| Resultado | Tempo | Custo | Commits | Testes | Subagentes |
|---|---|---|---|---|---|
| CONCLUIDO, branch `impl/expr-hist` (0882c10) no remote, sem PR; 2 bugs baixos abertos, registrados | 33m58s | US$ 13,05 (opus 12,71 · sonnet 0,34) | 9 itens + 5 consertos de QA + 4 merges + relatório + docs; 9 arquivos, +1093 −52 | 77 OK (eram 16) | enrich; 3 `impl-dev` em worktree (2 na onda 1, 1 na onda 2); 3 `impl-qa codigo` (sonnet, no clone); `impl-qa final` + reteste (opus, worktree) |

## O que a 0.6.0 resolveu (conferido no log)

| Item | Evidência |
|---|---|
| G1 sem dono | Nenhuma pergunta em texto; "Respostas (sem dono)" ao enriquecedor; 10 decisões na tabela "Decisões tomadas sem o dono" do relatório, com a alternativa |
| G2 arquivos fora da worktree | Nada perdido: 10 retros, 3 checkpoints, 9 logs de Aceite, 5 saídas de QA em `impl-snapshot/`, gravados por heredoc; pastas criadas pelo orquestrador antes do enriquecedor |
| N4 quadro sem `$(…)` | `QUADRO.md` completo: `INICIO`, 3 `CONTRATO`, 3 `AVISO`, `FIM` de cada faixa, `ONDA` e `MERGE` do orquestrador; os agentes rodaram `date -u` à parte |
| G3 e N6 sem PR | `gh repo view` na primeira chamada da fase 1; título do relatório com a branch e "sem PR"; comando de merge no relatório e na resposta |
| N5 git absoluto | Agentes usaram `/usr/bin/git -C <worktree>` vindo da linha `Comandos:` |
| N7 raiz do plugin | Orquestrador chamou `escopo.sh` e `preflight.sh` pelo caminho resolvido |
| N8 custo do enriquecedor | Enriquecedor leu `TRIAGEM.md` e só o §1 do `FAIXAS.md` (`sed`); nenhum subagente leu o `SKILL.md` |
| G4 releitura | Orquestrador leu cada arquivo auxiliar uma vez |
| G7 perfil | Quatro seções do perfil atualizadas no commit do relatório, marcadas "aplicado" na retro consolidada |
| N16 limpeza | Sem worktree nem branch `worktree-agent-*` ao fim; `.impl/expr-hist/` apagado; `git status` limpo |
| Contrato em ondas | Produtores (`parser`, `historico`) na W1, consumidor (`cli`) na W2 com as linhas `CONTRATO` do quadro; `escopo.sh` OK nas três faixas |
| QA | QA de código confirmou as decisões nas três faixas; QA final achou 5 bugs reais (stdout cheio, fechado, não codificável, arquivo 0444), consertados e retestados; 2 voltaram no reteste único e foram para o relatório |

## Gaps novos

Os sete foram aplicados na 0.6.1, no mesmo dia; nenhum foi conferido por um novo run.

| # | Sev. | Evidência | Proposta (arquivo do harness) |
|---|---|---|---|
| T1 | alta | O guard da worktree recusa mais do que o `AMBIENTE.md` lista: 28 recusas no run. `HOME=<temp> comando` ("sets HOME, injecting git configuration"), `env -u VAR …`, heredoc para `python3`, `python3 -m unittest` com operando calculado, roteiro longo, laço, `cd` para fora. Duas faixas fecharam `PARCIAL` só porque o Aceite usava `HOME=` | `AMBIENTE.md` § Bash na worktree de agente: ampliar a lista (prefixo de variável de ambiente, `env`, heredoc para interpretador, laço, `cd` fora). `FAIXAS.md` § 1, Aceite na ponta: Aceite que precisa de variável de ambiente ou de `HOME` leva a marca "só no clone" e quem o roda é o orquestrador, no merge |
| T2 | média | `PARCIAL` por parte do Aceite que só roda fora da worktree não é caso de continuação: o orquestrador rodou a parte que faltava na worktree de cada faixa e fez o merge, contra o `FAIXAS.md` § 3.1 novo ("`PARCIAL`: passo 9") | `FAIXAS.md` § 3.1: `PARCIAL` com todos os commits feitos e só verificação pendente = o orquestrador roda a verificação e segue; continuação só quando falta item |
| T3 | média | Riscos de CLI só apareceram no QA final: saída padrão cheia, fechada ou não codificável; arquivo do usuário somente leitura, modo, symlink; JSON com `true`, `NaN`, `1e999` | `impl-enrich.md`, Lista de riscos: linha para CLI (stdout e stderr cheios ou fechados, codificação) e, em "formato persistido", o arquivo que já existe (modo, somente leitura, symlink) e JSON não estrito |
| T4 | baixa | A resposta final ofereceu `/code-review ultra` sem número, embora o modo sem PR mande não oferecer | `SKILL.md` § 6.6: dizer "sem PR, não cite o `ultra`" na própria frase |
| T5 | baixa | O enriquecedor fez um protótipo em `/tmp/expr-hist-proto` (apagado depois), fora do repo e de `.impl/`, contra `_comum § Limites` | `impl-enrich.md`: protótipo descartável vai em `<repo>/.impl/<slug>/proto/` |
| T6 | baixa | Faixa cita em docstring um símbolo que outra faixa remove; o Aceite da W2 ficou vermelho até o conserto | `impl-enrich.md`: o arquivo de faixa não cita símbolo que o plano remove; a consulta de onda classifica cada ocorrência do `grep` por dono |
| T7 | baixa | Log de Aceite por heredoc obriga o agente a recopiar a saída; conserto de QA que amplia o `Pode tocar` foi feito à mão; QA `codigo` não sabia se podia rodar a branch | `impl-dev.md`: log por redirecionamento simples quando o guard deixa; `FAIXAS.md` § 3.3: conserto que toca arquivo novo atualiza a linha da faixa; `impl-qa.md`: modo `codigo` não roda nada, dito na primeira linha do modo |

## Não observado

Continuação de faixa por agente novo (N1; nenhuma faixa parou com item por fazer), cópia de prints do QA visual (N2; repo sem QA visual), `REPROVADO` e `AGUARDANDO`, serviço descartável e portas, GitHub real com PR, `/wh:limpeza` com perfil, CodeGraph. Consulta `PERGUNTA` houve uma (faixa `cli`, autorizada pelo enriquecedor, linha `AVISO` do quadro).

## Custo (G4b)

US$ 13,05 por 9 itens em 3 faixas, contra US$ 5,41 e 4,68 dos runs pequenos (3 e 5 itens, orquestrador no modelo mais caro). Opus leu 12,2M tokens de cache em todos os agentes juntos. O run não separa o custo por agente, então não dá o custo fixo de uma faixa única: a decisão do G4b continua sem medida. Para medir, repetir uma tarefa pequena com a mesma sessão em `--model opus`, inline, e comparar com os runs 1 e 2.
