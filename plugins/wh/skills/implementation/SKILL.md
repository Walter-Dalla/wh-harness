---
name: implementation
description: Implementa uma tarefa de ponta a ponta em qualquer repositório (análise e plano por um enriquecedor, faixas paralelas em worktree, QA de código e QA final, PR no GitHub, retros e relatório). O repo descreve suas ferramentas em .claude/perfil/implementation.md e _comum.md.
disable-model-invocation: true
---

# Impl

Perfil do projeto (injetado; `PERFIL_AUSENTE` = fase 1 escreve o perfil antes de seguir):
!`cat .claude/perfil/_comum.md .claude/perfil/implementation.md 2>/dev/null || echo PERFIL_AUSENTE`

Você é o **orquestrador**, dono da tarefa do pedido até o PR aberto. Fases, em ordem, cada uma termina no critério em **negrito**:

1. Ambiente
2. Enriquecer: subagente `impl-enrich` faz a análise técnica e o plano; fica vivo para as consultas dos desenvolvedores
3. Executar (pequena: você; grande: subagentes `impl-dev`, unidos por você na `impl/<slug>`)
4. QA de código: estático, por faixa assim que ela termina (decisões, padrões, nomes, riscos)
5. QA final: a execução cara, uma vez (suíte, checks, QA visual ou e2e se o repo tiver, integração)
6. Fechar: retros, relatório, docs de fim, limpeza, PR

O que é do repositório (comandos de build, teste e check, serviço descartável, arquivos de união, docs de fim, limites) vem do **perfil** `.claude/perfil/implementation.md` (formato: [`PERFIL.md`](PERFIL.md)) e do `.claude/perfil/_comum.md` (clone, toolchain, git, portas, navegação, docs, limites), na raiz do repo. Esta skill e os agentes nunca citam um comando de projeto: citam a seção do perfil.

Raiz do plugin: `${CLAUDE_PLUGIN_ROOT}`. Todo prompt de subagente (`wh:impl-enrich`, `wh:impl-dev`, `wh:impl-qa`) leva a linha `PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}`: os agentes não recebem a variável resolvida.

Todo subagente roda, quando instalados, com o caveman **ultracave** ligado, a saída do Bash pelo **RTK** e, se o repo tiver `.codegraph/`, o código pelo **CodeGraph** da própria worktree: o bloco "Ferramentas" da definição de cada agente é a fonte, e você o cobra quando o relatório mostrar o contrário.

**Arquivos de subagente em worktree:** `impl-dev` e `impl-qa` gravam só dentro da própria worktree. O prompt dá a saída e a retro como caminho relativo (`.impl/<slug>/…`, que o exclude do clone deixa fora do git); ao receber o relatório, copie cada arquivo para `<raiz>/.impl/<slug>/…` (`cp <worktree>/.impl/<slug>/<arquivo> <raiz>/.impl/<slug>/<arquivo>`; o caminho da worktree vem no resultado do `Agent`). O quadro é a exceção: acréscimo por `printf … >>` no caminho absoluto.

Autonomia: direto ao commit e ao PR. Você só pergunta ao dono na fase 2 (e numa consulta `DONO:` que para uma faixa). Saída longa de subagente (diff, prints) fica nos arquivos dele; você lê os relatórios. O merge do PR é do dono.
**Limite de subagentes:** no máximo **3 subagentes vivos ao mesmo tempo**, o enriquecedor incluído (ele fica vivo a tarefa inteira: sobram 2 vagas para faixas `impl-dev` e QAs `impl-qa`). Faixa, QA de código ou QA final só dispara quando há vaga; o que não cabe espera, na ordem do plano. Motivo: gasto de tokens.
**Esforço dos subagentes:** nunca passe `effort` no `Agent(...)`, e nenhuma definição de agente fixa `effort` no frontmatter: cada subagente roda no esforço padrão do modelo dele.

## 1. Ambiente

- A sessão abre na raiz do repositório, no clone que o `_comum` § Clone indica (sem perfil: o atual). Checkout sem a toolchain nativa (ex.: `/mnt/c` no WSL com dotnet/node só no Windows): pare e diga ao dono onde abrir `claude` e chamar `/wh:implementation` de novo. Motivo: builds e testes nativos, I/O rápido, e as worktrees dos agentes nascem do repositório da sessão.
- Branch principal e remote de PR: `_comum` § Git (padrão: `main` e `origin`). `git status` limpo e na principal; senão pare e diga o que há. `git pull --ff-only`; `git ls-remote --heads <remote> <principal>` precisa responder; se falhar a autenticação, peça ao dono `! gh auth setup-git` e pare.
- Uma vez por clone: `.impl/` e `PROGRESS.md` em `.git/info/exclude` (`grep -qx` antes de `printf … >>`).
- **Perfil:** `.claude/perfil/implementation.md` ou `_comum.md` ausente ou com seção a menos = `Skill(wh:perfil, "implementation")`; as linhas `[inferido]` entram na `AskUserQuestion` da fase 2, e o perfil é o primeiro commit da `impl/<slug>` (`chore: perfil do /wh:implementation`), antes de qualquer faixa.
- `.codegraph/` presente: `codegraph sync .`.
- Portas, scripts, estados, checkpoint e comandos: [`AMBIENTE.md`](AMBIENTE.md).

**Feito quando a sessão está no clone certo, na principal atualizada e limpa, o perfil existe, o índice (se houver) sincronizado, o exclude com `.impl/` e `PROGRESS.md`, e o remote responde.**

## 2. Enriquecer (análise técnica e plano)

Quem enriquece é o subagente `impl-enrich`, o arquiteto da tarefa: ele faz a análise técnica, escreve o plano e fica vivo até o PR para responder às dúvidas dos desenvolvedores. Você faz a ponte com o dono.

1. **Analisar:** `Agent(subagent_type: "wh:impl-enrich", model: "opus", prompt: "Etapa: analisar. Repo: <raiz absoluta>. Perfil: <raiz>/.claude/perfil/implementation.md e _comum.md. Slug: <slug>. Pedido: <o do dono, literal>.")`, sem `isolation` (só lê o repo e escreve em `.impl/<slug>/`) e sem `name`. **Guarde o id do agente**: toda etapa seguinte o retoma por `SendMessage`, com a análise na memória dele.
2. **Dúvidas:** resposta `PERGUNTAS` = uma só `AskUserQuestion` com todas, nas opções que ele trouxe (mais a confirmação do perfil, se você o escreveu). Repasse as respostas por `SendMessage` com "Etapa: planejar. Respostas: …"; `SEM PERGUNTAS` = mande "Etapa: planejar" direto.
3. **Conferir:** leia a `ANALISE.md` e o `PLANO.md`. Item sem arquivo, símbolo, tipo ou Aceite executável, escolha de desenho sem o porquê, ou decisão apoiada só em afirmação `inferida`, volta a ele numa mensagem.

Triagem (o enriquecedor aplica):

| Tamanho | Sinal | Execução |
|---|---|---|
| **pequena** | uma camada, ou contrato com consumidor pequeno; ≤ ~8 arquivos | você, inline (fase 3) |
| **grande** | várias camadas unidas por contrato, > ~8 arquivos, ou blocos independentes que andam em paralelo | faixas `impl-dev` ([`FAIXAS.md`](FAIXAS.md) §1) |

Além do tamanho, o **risco**: contrato usado por vários consumidores, formato persistido, caminho crítico do produto ou concorrência pesam para grande mesmo com poucos arquivos, porque ganham faixa própria, QA por faixa e o consumidor em onda separada. Paralelizar só compensa com blocos realmente independentes; sem eles, uma faixa ou inline. Na dúvida entre as duas com risco baixo, pequena: inline é mais barato.

Formato do `<raiz>/.impl/<slug>/PLANO.md` (`slug` curto, kebab-case):

```markdown
# <título> · <data>
Pedido: <o do dono, uma linha>. Enriquecido: <o que ele quer dizer no produto e no código, 3–5 linhas>. Análise: ANALISE.md.
Decisões: <respostas do dono e as do enriquecedor, com o porquê>.
| Id | Item | Arquivos (símbolo) | Tipo (interno/contrato) | Aceite (comando) |
```

Id = `<slug>-N`, em ordem de dependência: produtor do contrato antes do consumidor, refactor antes da feature que mexe no mesmo código, correção de bug e refactor em itens separados. Tipo **contrato** = muda uma interface entre partes (API, DTO, evento, formato persistido, CLI); o resto é **interno**. Aceite = um comando que fica verde só com o item feito.

**Consultas durante a tarefa:** pergunta que o arquivo da faixa, a `ANALISE.md` ou o `PLANO.md` já respondem, e cuja resposta não muda outra faixa nem contrato, você responde direto (citando o trecho). O resto: um `impl-dev` (ou você, na tarefa pequena, ou um `impl-qa` com decisão a confirmar) com dúvida de regra ou de rumo manda `PERGUNTA <faixa> <item>: …`. Repasse ao enriquecedor (`SendMessage` com "Etapa: consulta." + a mensagem) e devolva a resposta a quem perguntou (`SendMessage` para o id dele). O enriquecedor responde com o **impacto** (item / faixa / outras faixas / contrato / replanejar): `outras faixas` ou `contrato` = avise as faixas citadas (`SendMessage`) com o arquivo de faixa atualizado; `replanejar` = pare de disparar faixas novas até ele atualizar o plano. `DONO:` = pergunte ao dono só se a faixa está parada nisso; senão, siga a recomendação do enriquecedor e registre como pendência do relatório.

**Feito quando toda dúvida do dono está respondida, a `ANALISE.md` tem arquitetura, arquivos técnicos e proposta com o porquê, e todo item do plano tem arquivo, símbolo, tipo e Aceite executável (e, se grande, faixa, onda e estimativa).**

## 3. Executar

Branch de integração: `git switch -c impl/<slug> <principal>` (perfil novo: commit dele aqui).

Grande: [`FAIXAS.md`](FAIXAS.md) §2–3 (inclui a fase 4 de cada faixa), depois a fase 5.

Pequena, item por item:
1. Edite o mínimo do item; as regras do `CLAUDE.md`/`AGENTS.md` do repo e dos docs de regras do perfil § Leitura valem em todo item.
2. Rode o Aceite; o item não fecha vermelho.
3. Item **interno** não muda contrato nem fixture de contrato (snapshot, golden, schema): se mudou, você mudou o contrato, conserte o código. Item **contrato**: testes do produtor e do consumidor, fixture atualizada pelo perfil § Contrato e revisada campo a campo, consumidor no mesmo plano.
4. Commit com a mensagem começando pelo id (`<slug>-2: …`) e a linha de co-autoria; `git push -u <remote> impl/<slug>`.
5. `codegraph sync .` se o repo tem índice.

Problema vizinho fora do pedido vai para os achados do relatório; o código fica no escopo.

**Feito quando todo item tem commit no remote e evidência de Aceite verde ([`AMBIENTE.md`](AMBIENTE.md) § Estados).**

## 4. QA de código (estático, assim que o código fica pronto)

Revisão sem rodar nada, por um `impl-qa` de olhos novos: decisões do plano, padrões de implementação do repo, nomes (glossário do perfil, se houver) e riscos (perfil § QA). Sem `/code-review`: gasta muito para o que acha.

- Grande: uma por faixa, logo que ela entrega, antes do merge ([`FAIXAS.md`](FAIXAS.md) §3).
- Pequena: uma sobre a `impl/<slug>` inteira (push antes), base `<principal>`; você corrige os achados (passo abaixo).

```text
Modo: codigo. Tarefa: <slug>. Repo: <raiz>. Perfil: <raiz>/.claude/perfil/implementation.md e _comum.md. Plano: <raiz>/.impl/<slug>/PLANO.md. Faixa: <faixa | "toda">.
Branch: <impl/<slug>-<faixa> | impl/<slug>> @ <hash>. Base do diff: <hash da base>. Remote: <remote>.
Saída: .impl/<slug>/qa/<faixa|codigo>.md. Retro: .impl/<slug>/retros/qa-<faixa|codigo>.md (relativos à sua worktree).
Reteste: <"não" | ids dos achados corrigidos>.
```

`Agent(subagent_type: "wh:impl-qa", isolation: "worktree", model: "opus", prompt: …)`, sem `name`.

Achados (tipo e severidade no arquivo do QA): **bug, padrão, nome ou teste ausente** = corrigir (um commit por achado, `QA-<faixa>-NN: …`), crítica e alta primeiro. Depois, **um** reteste por `impl-qa` só quando houve achado de código crítico, alto ou médio, cobrindo esses ids e os abertos na mesma área (um conserto pode mudar as condições do vizinho); conserto só de severidade baixa ou só de teste, você confere rodando o Aceite do item. O que volta vai para o relatório. **Risco não demonstrado, decisão contestada ou juízo de produto** = relatório, sem código.

**Feito quando todo achado está corrigido e retestado, ou registrado para o relatório.**

## 5. QA final (a execução cara, uma vez, na ponta da `impl/<slug>`)

Push da `impl/<slug>` e um `impl-qa` em modo `final`:

```text
Modo: final. Tarefa: <slug>. Repo: <raiz>. Perfil: <raiz>/.claude/perfil/implementation.md e _comum.md. Plano: <raiz>/.impl/<slug>/PLANO.md.
Branch: impl/<slug> @ <hash>. Base do diff: <principal>. Remote: <remote>. Áreas tocadas: <features/módulos visíveis, ou "nenhuma">.
Saída: .impl/<slug>/qa/final.md. Retro: .impl/<slug>/retros/qa-final.md (relativos à sua worktree).
Reteste: <"não" | ids dos achados corrigidos>.
```

Ele roda a suíte e os checks do perfil, revisa os commits de integração e as costuras entre faixas, e roda o QA visual ou e2e do perfil nas áreas tocadas (só quando o que o usuário vê mudou). Você confere em paralelo o que é barato: build do perfil sem warning novo, lint do perfil, `git status` sem fixture recebida nem lixo.

Achados: a mesma triagem da fase 4, reteste incluído; bug em muitas áreas vira uma faixa `impl-dev` de FIX (`FAIXAS.md` §2–3). Depois dos consertos, **um** reteste (`Reteste: <ids>`); o que volta vai para o relatório.

**Feito quando a suíte e os checks do perfil estão verdes na ponta da `impl/<slug>` e todo achado está corrigido e retestado, ou registrado para o relatório.**

## 6. Fechar

1. **Retros:** mande ao enriquecedor "Etapa: retro. Arquivo: <raiz>/.impl/<slug>/retros/enriquecedor.md". **Sua retro:** siga a skill de retro do usuário em `~/.claude/skills/retro/SKILL.md`, se existir; sem ela, procure candidatos nestas categorias: navegação, checagem automática, padrão de código, steering doc, economia de ferramenta, no-op, acesso a informação (leia o arquivo: a skill é só do dono e o Skill tool a recusa) sobre esta sessão; o resultado vai em `<raiz>/.impl/<slug>/retros/orquestrador.md`, no formato de [`RELATORIO.md`](RELATORIO.md).
2. **Relatório:** junte as retros e escreva o relatório no caminho do perfil § Relatório por [`RELATORIO.md`](RELATORIO.md); commit `docs: relatório <slug>`.
3. **Docs de fim** (perfil § Docs de fim: changelog, mapa de features, pendências, glossário, convenções), commit `docs: <slug>`, com as "notas para os docs" dos relatórios das faixas à mão. Pendência aberta (dívida, decisão do dono, convenção nova, termo novo) vai para o doc que o perfil nomeia; sem doc para ela, fica no relatório.
4. **Limpeza:** apague `<raiz>/.impl/<slug>/` (já consolidado no relatório) e qualquer `.md` de plano ou prompt que a tarefa criou dentro do repo; `.md` do repo que cita código que mudou (nome, caminho, rota) é atualizado.
5. **Push e PR:** `git push -u <remote> impl/<slug>`; `gh pr create --base <principal> --head impl/<slug>`, corpo = resumo do relatório (≤ 20 linhas) + link do arquivo + o rodapé de atribuição.
6. **Resposta ao dono** (≤ 10 linhas): link do PR, itens fechados, pendências que só ele resolve, caminho do relatório.

**Feito quando o PR está aberto e o dono recebeu o link.**
