# Test-drive · calculadora · 2026-10-28

Primeira execução de ponta a ponta do `/wh:implementation` (plugin `wh` 0.3.1, working tree não commitado, Claude Code 2.1.312) num repo mínimo: calculadora Python CLI + `unittest`. Dois runs headless (`claude -p … --output-format stream-json --verbose --permission-mode bypassPermissions --dangerously-skip-permissions`), sem dono presente, remote `origin` = bare local (`gh pr create` não se aplica, de propósito). Modelo do orquestrador: `fable` (settings do dono); subagentes: `opus`/`sonnet` como a skill manda.

Logs brutos (fora do git): `/home/walter/calc-harness-logs/run-{1,2}/` — `session.jsonl` (stream do orquestrador, inclui tool calls dos subagentes), `events.jsonl` (hooks Pre/PostToolUse, SubagentStart/Stop, Stop, SessionStart em todos os agentes), `impl-snapshot/` (cópia de `.impl/<slug>/` a cada evento, sobrevive à limpeza), `git/`, `repo-final.tgz`, `analysis.txt` (saída de `analyze.py`). Repo alvo: `/home/walter/calc-harness-test` (branches `impl/calc-base` em `main`, `impl/pow-sqrt` aberta).

| Run | Pedido | Perfil | Resultado | Tempo | Custo | Commits | Testes | Subagentes |
|---|---|---|---|---|---|---|---|---|
| 1 | calculadora base (core + CLI + testes) | ausente → gerado pela skill (`adiar`) | CONCLUIDO, branch no remote, sem PR | 9m29s | US$ 5,41 (fable 4,19 · opus 1,14 · sonnet 0,07) | 8 (perfil, 2 itens, 3 consertos de QA, relatório, docs) | 17 OK | enrich ×3 turnos, qa codigo (sonnet), qa final + reteste (opus, worktree) |
| 2 | `pow` e `sqrt` (core, CLI, testes) | presente, pulou `/wh:perfil` | CONCLUIDO, branch no remote, sem PR | 7m42s | US$ 4,68 (fable 3,38 · opus 1,30) | 9 (5 itens, 2 consertos, relatório, docs) | 29 OK | enrich ×3, qa final (opus, worktree); sem QA de código, sem reteste |

Relatórios que o harness mesmo escreveu (lidos e conferidos contra o log): `calc-harness-test/docs/relatorios/2026-10-28-{calc-base,pow-sqrt}.md`. A retro consolidada deles já aponta a maior parte dos gaps abaixo; a numeração aqui é nossa.

## Timeline

Run 1 (hora local, de `events.jsonl`):

| Fase | Janela | O que aconteceu |
|---|---|---|
| 1 Ambiente + perfil | 13:42:13–13:42:49 (36s) | status/pull/ls-remote ok; `.impl/` no exclude; `Skill(wh:perfil, "implementation adiar")` inline: leu `COMUM.md` e `PERFIL.md` do plugin, escreveu `_comum.md` (26 l) e `implementation.md` (43 l) com fonte por linha, quase tudo `[inferido]` |
| 2 Enriquecer | 13:42:49–13:44:26 | `impl-enrich` (opus) analisar 50s → `ANALISE.md` 76 l (arquitetura, código proposto, alternativas descartadas, riscos) + `PERGUNTAS` com 2 decisões (D1 formato `6 / 3`, D2 alias `x`). **Sem `AskUserQuestion` na sessão**: orquestrador escolheu as opções recomendadas e repassou. Planejar 37s → `PLANO.md`, triagem pequena, 3 itens. Enriquecedor corrigiu sozinho o Aceite do item 3 (exit do `grep`) |
| 3 Executar | 13:44:26–13:45:37 | branch `impl/calc-base`, commit do perfil, itens 1 e 2 inline, commit por item com id e co-autoria, push. Item 1 = contrato → `impl-qa codigo` (sonnet, 11s): 1 achado baixo (teste fraco), corrigido `QA-core-01` |
| 5 QA final | 13:45:37–13:46:36 | `impl-qa final` em worktree: `preflight.sh` OK, suíte 15 OK, 30 casos à mão. Achou bug médio real (`OverflowError` com inteiro de 400 dígitos) + 2 juízos de produto. Conserto `QA-final-01` |
| 5 Reteste | 13:47:01–13:48:21 | segundo `impl-qa final`: confirma conserto, acha vizinho médio (`ValueError` do limite de 4300 dígitos em `_fmt`). **`Write` em `<raiz>/.impl/` recusado pelo isolamento da worktree**; gravou dentro da worktree, removida ao fim → saída e retro perdidas; orquestrador reconstruiu do relatório do agente |
| 6 Fechar | 13:48:21–13:51:42 | retro do enriquecedor (via `SendMessage`), `Skill(wh:retro)` do orquestrador, relatório em `docs/relatorios/` (aplicou 3 linhas de retro no perfil), README, limpeza inline (`.impl/` apagado, worktrees removidas), push. Sem PR: explicou e deu o comando de merge |

Run 2: perfil presente (fase 1 em 11s); enrich 91s + 47s (3 perguntas, mesmas respostas automáticas; verificou semântica do Python com `python3 -I -c` antes de afirmar); 5 itens em 82s (itens 1 e 2 saíram num commit só → orquestrador refez a história com `git reset --soft HEAD~2` antes do push); sem QA de código ("consumidor no mesmo plano"); QA final 2m22s, 2 achados baixos corrigidos, sem reteste; fechar em ~80s. Novamente `Write`/`mkdir` recusados na worktree; dessa vez o QA contornou com `mkdir -p` + `cat > … <<'EOF'` e nada se perdeu.

## O que funcionou

- Fluxo inteiro sem intervenção: perfil → análise → plano → itens com commit e Aceite → QA → consertos → retros → relatório → docs → limpeza → push. Nenhum `BLOQUEADO`.
- Perfil gerado com fonte por linha e seções `—` honestas; run 2 pulou a geração.
- Análise e plano de qualidade: alternativas com porquê (parse manual × `argparse`, `x` × `*` no shell), riscos listados, Aceite executável por item.
- QA final em worktree achou 3 bugs reais que a suíte do implementador não pegava (overflow, 4300 dígitos, `pow(2, 10**400)`); reteste achou o vizinho. Triagem bug/juízo de produto respeitada: juízo foi para o relatório, não para o código.
- Retros em todos os agentes, consolidadas e deduplicadas no relatório; propostas citam arquivo e quem aplica.
- Commits no formato (`<slug>-N:`, `QA-<faixa>-NN:`, `docs:`, co-autoria), `.impl/` fora do git, worktrees removidas, `git status` limpo ao fim.
- Sem GitHub: os dois runs perceberam, registraram no título do relatório e deram o comando de merge.
- Hooks do projeto dispararam em todos os subagentes e worktrees (148 e 102 eventos): a observabilidade externa funciona sem mudar o harness.

## Gaps

| # | Sev. | Fase | Evidência | Proposta (arquivo do harness) |
|---|---|---|---|---|
| G1 | alta | 2 | Sem dono (`-p`), `AskUserQuestion` não existe; nos dois runs o orquestrador improvisou (opção recomendada do enriquecedor + "Decisões tomadas sem o dono" em Pendências). Run 1 `session.jsonl` turno 14; run 2 turno 11. A skill não prevê o caso | `skills/implementation/SKILL.md` § 2: "Sem `AskUserQuestion` (sessão autônoma): adote a opção recomendada de cada pergunta, marque `(sem dono)` em Decisões do plano e liste em Pendências do relatório; linhas `[inferido]` do perfil ficam sem confirmar". Idem `skills/perfil/SKILL.md` § 3 já cobre o perfil |
| G2 | alta | 4–5 | Worktree isolada (CC 2.1.312) recusa `Write`/`Edit` e `mkdir` em caminho fora dela (`<raiz>/.impl/…`), e recusa Bash composto ("too complex to verify"). Run 1: arquivos do reteste perdidos com a worktree. Run 2: só `mkdir -p` + heredoc simples passou, e `qa/` não existia. Confirma o "a verificar" de `SKILL.md` § Arquivos de subagente | `agents/impl-qa.md`, `agents/impl-dev.md`: "grave com `Bash`: `cat > <abs> <<'EOF'`, uma chamada simples por arquivo; nunca `Write`/`Edit` fora da worktree". `SKILL.md` § 1: orquestrador cria `.impl/<slug>/{qa,retros,progress}` antes de disparar agentes e põe `.claude/worktrees/` no exclude (run 1 fez à mão). `AMBIENTE.md` § Scripts: `git -C <worktree> reset --hard` em chamada própria (retro qa-final run 1) |
| G3 | média | 1, 6 | Sem GitHub só se descobre na fase 6.5; os dois runs lidaram bem, mas a skill manda `gh pr create` sem alternativa e o `/code-review ultra` do relatório fica sem sentido | `SKILL.md` § 1: `gh repo view` (ou `git remote get-url` não-GitHub) → modo "sem PR" declarado desde o início; § 6.5: fallback = branch no remote + comando de merge no relatório |
| G4 | média | todas | Custo: orquestrador no modelo do dono (`fable`) = 77% (run 1) e 72% (run 2) do total; 3,06M e 1,5M tokens de cache lidos. Tarefa pequena = o modelo mais caro escreve código inline. Run 1 releu `SKILL.md`/`RELATORIO.md` via `cat` 3× (turnos 16, 57, 66) com a skill já no contexto | `docs/MANUAL.pt-BR.md` § 4: recomendar `claude --model opus` para sessões de `/wh:implementation` (perfil § Modelos não alcança o orquestrador). Avaliar: tarefa pequena também por `impl-dev` (1 faixa) para tirar o código do orquestrador |
| G5 | média | 2–3 | O exemplo de § Testes em `skills/implementation/PERFIL.md` (`dotnet test 2>&1 \| grep …`) induz comando cujo exit é do `grep`; o perfil gerado herdou e o enriquecedor consertou com `PIPESTATUS`; run 1 aplicou correção no perfil do repo | `PERFIL.md` § Testes: "Veredito: comando cujo exit é o da suíte (`… -q`); filtro de leitura à parte". `AMBIENTE.md` § Testes: mesma regra |
| G6 | média | hook | `contexto.json` nunca foi criado: `/wh:perfil` não cria, o MANUAL deixa para o humano; `prompt_graph.py` não disparou em nenhum prompt dos dois runs (0 injeções) | `skills/perfil/SKILL.md` § 4: escrever `contexto.json` quando houver glossário/features/codegraph, ou registrar "hook desligado: sem fontes" na resposta. MANUAL § 4 passo 6 vira automático |
| G7 | média | 6 | Run 1 aplicou 3 linhas de retro no perfil (severidades média e baixa); `SKILL.md` § 6.2 só autoriza "alta". Run 2 não aplicou nada e deixou § Contrato desatualizado como pendência. Regra lida de dois jeitos | `SKILL.md` § 6.2: decidir. Sugestão: qualquer severidade quando a proposta é uma linha do perfil (perfil é do repo, revisável no PR); o resto só o dono |
| G8 | baixa | 3 | Run 2: itens 1 e 2 editados juntos, commit 1 levou os dois, orquestrador reescreveu história não publicada (`git reset --soft HEAD~2`); a skill é omissa | `SKILL.md` § 3 (pequena): "um item por edição; `git diff --stat` antes do commit; dois itens no mesmo trecho = um commit com os dois ids, sem reescrever" |
| G9 | baixa | 4–5 | `perfil § QA` citado em `SKILL.md:94` e `agents/impl-qa.md:28` não existe no `PERFIL.md`; os agentes resolveram por semelhança com `§ QA visual ou e2e`; `tests/test_refs.py` aceita por prefixo | Renomear para `§ QA visual ou e2e` nos dois lugares; `test_refs.py` exigir nome completo |
| G10 | baixa | 4 | Exceção "item contrato na pequena = QA de código": run 1 fez (11s, 1 achado baixo), run 2 pulou ("consumidor no mesmo plano"). Leituras diferentes da mesma regra | `SKILL.md` § 4: limitar a exceção a contrato com consumidor fora do plano (retro run 2 nº 3) |
| G11 | baixa | 2 | "Aceite verde só com o item feito" não cabe em item de refactor (pow-sqrt-3); enriquecedor usou suíte antes/depois | `SKILL.md` § 2 formato do plano: "refactor: suíte da área verde antes e depois" |
| G12 | baixa | 2 | Aceite por regex de prefixo deixou passar teste fraco (QA-core-01 run 1) | `agents/impl-enrich.md`: texto fixado na análise = assert de igualdade no Aceite |
| G13 | baixa | infra | Headless: run 1 produziu 3 objetos `result` e 5 `Stop` (orquestrador encerrou o turno esperando subagentes em background; o CC retomou nas notificações). Funciona, mas consumidor de `-p` que lê o primeiro `result` vê tarefa pela metade | Observação para o MANUAL (§ 6): em `-p`, usar o último `result` |
| G14 | baixa | instal. | Cache do plugin ficou em 0.2.0 até `claude plugin update wh@wh-harness`; MANUAL § 4 diz que edição no diretório "vale na sessão seguinte, sem push" | MANUAL § 4 (mantenedor): acrescentar `claude plugin update wh@wh-harness` após editar, ou documentar `--plugin-dir` |
| G15 | baixa | teste | `.impl/<slug>/` some na limpeza; sem o snapshot externo não há trilha do que cada agente gravou | `SKILL.md` § 6.4 opcional: `tar` de `.impl/<slug>/` para `docs/relatorios/<slug>.impl.tgz`? Provável não: o relatório consolida. Deixar como está, registrar |

Não observado: tarefa grande (faixas `impl-dev`, `QUADRO.md`, `progress/`, `escopo.sh`, consultas `PERGUNTA`), `/wh:limpeza` com perfil (limpeza foi a inline), `/wh:feature-docs`, `/wh:qa-visual`, `/wh:start-app`, CodeGraph. Caveman (hooks do dono) não vazou para nenhum `.md` gravado.

## Próximos passos sugeridos (nada aplicado)

1. G1, G2, G3 na skill e nos agentes; subir `version` em `plugin.json`, ajustar o MANUAL.
2. G5, G9 (uma linha cada) e `test_refs.py` estrito.
3. Repetir o test-drive com tarefa grande (ex.: calculadora com parser de expressões + histórico em arquivo + CLI, para forçar 2–3 faixas e contrato com consumidor) e com GitHub real para fechar o PR.
4. Reaproveitar `/home/walter/calc-harness-logs/{log_event.py,run.sh,analyze.py}` como `examples/testdrive/` do harness, se valer manter.
