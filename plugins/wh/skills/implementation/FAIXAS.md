# Tarefa grande: faixas paralelas `impl-dev`

Cada faixa = um subagente `impl-dev` na própria worktree e na própria branch (`impl/<slug>-<faixa>`, no remote a cada commit). O enriquecedor escreve as faixas (§1); você dispara, une e valida; código você escreve só no conserto de merge.

## 1. Dividir em faixas (o enriquecedor faz, na etapa `planejar`)

O equilíbrio é **paralelismo × reuso de contexto × tokens**:

- **Mesmo lugar, mesmo desenvolvedor.** Itens no mesmo arquivo, no mesmo invariante, no mesmo contrato ou no mesmo módulo vão numa faixa, em ordem de dependência: o segundo item reaproveita o que o primeiro já leu. Refactor vai na mesma faixa (e antes) da feature que mexe no mesmo código.
- **Paralelo só no que não se toca.** Faixas da mesma onda são donas de arquivos disjuntos. Arquivos de união (perfil § Arquivos de união) podem ser de várias: cada faixa só acrescenta, você resolve no merge.
- **Contrato em ondas.** A faixa produtora dona do contrato numa onda; o consumidor numa onda seguinte.
- **Tamanho.** Medida observável, não tokens: itens, arquivos do `Dono de:` e o tamanho em linhas de cada um (item contrato ou arquivo grande pesa o dobro).
- **Limite.** No máximo 3 subagentes rodando (`SKILL.md` § Limite de subagentes): uma onda tem no máximo 3 faixas em paralelo (uma porta do perfil por faixa), e o QA de código de uma faixa pronta também ocupa vaga; onda maior vira ondas menores, ou as faixas extras esperam vaga.
  - **Teto:** ≤ 6 itens e ≤ 15 arquivos (ou ~5k linhas) por faixa. Acima disso, parta a faixa pelo ponto de menor acoplamento (itens em série viram duas faixas em ondas seguidas).
  - **Piso:** faixa com menos de 3 itens é pequena demais (paga o custo fixo de instruções, ferramentas e índice por pouco trabalho): junte à vizinha com quem divide arquivos, ou ponha o item na onda seguinte de outra faixa.

Uma faixa = `<raiz>/.impl/<slug>/<faixa>.md`; o agente não vê esta conversa, então tudo o que ele precisa está aqui. Os caminhos de `Dono de:`, `Pode tocar` e `União:` vão entre crases: o `scripts/escopo.sh` os lê (`União:` copia o perfil § Arquivos de união; caminho terminado em `/` vale a pasta inteira). Todo arquivo que um item manda mudar entra numa dessas linhas, inclusive o que o texto do item cita só em prosa; resposta de consulta que amplia o escopo atualiza a linha.

**Aceite na ponta:** antes de escrever a faixa, rode o Aceite de cada item na ponta de onde a onda nasce (a principal no `planejar`; depois, a `impl/<slug>`), com serviço descartável se ele precisar. Vermelho = o item entra; verde = o item já está feito ou o Aceite não o prova: sai do plano com a prova no `PLANO.md`, ou o Aceite é reescrito (item de refactor: verde antes é o esperado, o item fica). Aceite que o guard da worktree recusa (`AMBIENTE.md` § Bash na worktree de agente: variável de ambiente na frente, `env`, `HOME` trocado, laço): reescreva-o numa forma que passa (o teste monta o próprio ambiente); se não der, marque no item "Aceite só no clone" e dê à faixa um segundo comando, que roda na worktree, para o desenvolvedor fechar o item. `Dono de:` sai dos arquivos que cada item manda mudar, nunca de uma lista anterior; arquivos de skill e de agente entram como qualquer arquivo. Contagem (linhas, ocorrências, parâmetros) vai como o comando que a mede, nunca o número; o Aceite de um caminho removido é `git grep -n <caminho>` sem filtro de extensão.

```markdown
# <faixa> · <slug> · onda W<n> · porta <do perfil ou —> · <n> itens · <m> arquivos (~<linhas>)
Contexto: <o pedido enriquecido e as decisões que tocam esta faixa>.
Dono de: `<caminho ou glob>` `<…>` (símbolos à parte). Pode tocar o mínimo de: `<caminho de outra faixa>` (ou "—"). União: `<glob>` `<…>` (ou "—").
Par: <faixa que consome ou fornece contrato, ou "—">.
## <id> · <título> · interno|contrato
<o que mudar, símbolos e arquivo:linha do enriquecimento, regra que vale>. Aceite: `<comando>`.
```

No `PLANO.md`, acrescente a tabela `| Onda | Faixa | Itens | Porta | Arquivos (linhas) |`. Crie `<raiz>/.impl/<slug>/QUADRO.md` vazio (as pastas `qa/`, `retros/`, `progress/` e `aceite/` o orquestrador criou na fase 1).

## 2. Disparar

Commit e push da `impl/<slug>` antes da primeira onda (é a base). Antes de cada onda, a base é a ponta real da `impl/<slug>` (`git rev-parse impl/<slug>`), com a onda anterior inteira mergeada e verde. Antes de cada onda depois da primeira, o plano envelheceu: mande ao enriquecedor "Etapa: consulta. ONDA W<n> na ponta <hash>: Aceites, linhas CONTRATO do quadro, arquivos movidos"; ele roda os Aceites na ponta, tira das faixas os itens verdes e anexa a cada arquivo de faixa as linhas `CONTRATO` do quadro que ela consome e os arquivos que mudaram de lugar. Anote no quadro `orquestrador | ONDA | W<n> base <hash>`. Dispare respeitando o limite de 3 subagentes vivos (`SKILL.md` § Limite de subagentes): a próxima faixa ou QA só quando um agente terminou. Prompt de cada agente:

```text
PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}
Faixa: <faixa>. Arquivo: <raiz>/.impl/<slug>/<faixa>.md. Repo: <raiz>. Perfil: <raiz>/.claude/perfil/implementation.md e _comum.md.
Branch: impl/<slug>-<faixa>. Base: impl/<slug> @ <hash>. Remote: <remote>.
Comandos: perfil § Comandos na worktree antes do 1º comando; git = <caminho absoluto da fase 1> -C <worktree> …, um comando por chamada.
Porta: <porta ou —>. Quadro: <raiz>/.impl/<slug>/QUADRO.md.
Retro: <raiz>/.impl/<slug>/retros/<faixa>.md. Checkpoint: <raiz>/.impl/<slug>/progress/<faixa>.md.
Continuação: <"do zero" | checkpoint anterior + branch de onde seguir + o que mudou na base ou na faixa desde então>.
```

`Agent(subagent_type: "wh:impl-dev", isolation: "worktree", model: <perfil § Modelos; sem regra, "opus">, prompt: …)`, **sem `name`** (com nome vira colega de agent team). Guarde o id de agente de cada faixa (consertos e respostas voltam a ele). Enquanto rodam, espere os relatórios; os diffs você lê no merge.

**Ponte de dúvidas:** mensagem `PERGUNTA …` de uma faixa = consulta ao enriquecedor (fase 2 do `SKILL.md`, "Consultas durante a tarefa"), resposta ao id da faixa. Relatório `AGUARDANDO: …` = a mesma consulta; a resposta retoma a faixa.

## 3. QA de código, unir e validar (por faixa, na ordem da onda)

1. **Estado e escopo:** o estado do relatório da faixa decide. `CONCLUIDO` (evidência por item) ou `DECISAO_HUMANA`: segue pelos passos abaixo com o que ficou pronto; a linha `HUMANO` vai para o relatório. `PARCIAL` com todo item commitado e só verificação pendente (Aceite "só no clone", comando que o guard recusou; linha `AVISO` no quadro): rode você a verificação na worktree da faixa, ou no clone na ponta da branch dela; verde = segue como `CONCLUIDO`, vermelho = volta ao agente como `REPROVADO`. `PARCIAL` com item por fazer, ou `BLOQUEADO`: passo 9. `AGUARDANDO`: consulta ao enriquecedor (§2, Ponte de dúvidas); a resposta retoma a faixa. `REPROVADO`: nunca merge; devolva ao mesmo agente (`SendMessage`) o vermelho do relatório dele, e uma segunda reprovação vira faixa de FIX ou pendência do relatório. Depois, `${CLAUDE_PLUGIN_ROOT}/skills/implementation/scripts/escopo.sh <faixa.md> <base> <remote>/impl/<slug>-<faixa>` sem `FORA:` (senão a faixa conserta, `SendMessage`).
2. **QA de código** (fase 4 do `SKILL.md`) logo que a faixa entrega: `impl-qa` modo `codigo` na `impl/<slug>-<faixa>`, base = o hash de onde a faixa partiu, com o diff gravado antes (molde da fase 4). Roda enquanto as outras faixas da onda ainda trabalham.
3. **Consertos da faixa:** os achados de bug, padrão ou nome voltam ao **mesmo** `impl-dev` (`SendMessage` com o id do agente devolvido no spawn: ele retoma com o contexto da faixa), com a lista de ids e o arquivo do QA; ele faz um commit por achado e push. Conserto que precisa de arquivo fora do `Dono de:`: acrescente o caminho, entre crases, ao `Pode tocar` do arquivo da faixa antes de mandar (o `escopo.sh` roda de novo no merge). Depois, o reteste pela regra da fase 4 do `SKILL.md` (agente só com achado de código crítico, alto ou médio). Agente retomado que não acha mais a própria worktree (removida): continuação pelo passo 9.
4. **Arquivos da faixa:** retro, checkpoint e saída do QA já estão em `<raiz>/.impl/<slug>/` (caminhos absolutos do prompt); confira que a retro existe. O que um agente devolveu na resposta porque a escrita foi recusada, você grava.
5. **Merge:** `git fetch <remote>` e `git merge --no-ff <remote>/impl/<slug>-<faixa> -m "impl: <faixa>"` na `impl/<slug>`; anote no quadro `orquestrador | MERGE | <faixa> → <hash>`.
6. **Conflito:** resolva mantendo a intenção das duas faixas (a do relatório de cada uma); arquivo de união = as duas listas de linhas. Conflito que exige reescrever lógica: aborte o merge e mande a faixa que entrou depois (`SendMessage`) fazer "rebase em impl/<slug> e resolva <arquivos>".
7. **Revisão rápida:** `git diff --stat`; nenhuma fixture de contrato recebida ou lixo de teste. Fixture tocada por duas faixas da onda: a segunda roda de novo pelo perfil § Contrato na integração e você revisa o diff.
8. **Fim de onda:** build e suíte do perfil na ponta da `impl/<slug>`, depois push (onda de uma faixa só, mergeada sem conflito: a suíte que a faixa rodou no fim vale; só o build). Doc protegido (perfil § Arquivos protegidos) que a onda deixou desatualizado, você corrige aqui com as notas das faixas, em commit próprio. Checks caros e QA visual/e2e ficam para o QA final (fase 5). Verde: próxima onda (a base nova é esse hash). Vermelho: conserto de uma linha você faz em commit próprio (`<slug>-fix: …`); senão a faixa culpada conserta (`SendMessage`).
9. **Faixa parcial ou bloqueada:** `BLOQUEADO` = resolva o ambiente. Continuação = agente novo com o mesmo prompt + o checkpoint dela, base = ponta da branch dela, e o que mudou desde então. Antes de dispará-lo, libere o nome da branch (a worktree antiga o segura, e o `git branch -m` do agente novo falharia): na worktree antiga (`git worktree list --porcelain`), mudança não commitada vira commit `wip: <faixa>` e push; confira que `git rev-parse impl/<slug>-<faixa>` e `git rev-parse <remote>/impl/<slug>-<faixa>` dão o mesmo hash; então `git worktree remove --force <worktree antiga>` e `git branch -D impl/<slug>-<faixa>` (a branch continua no remote). O QA de código roda depois da continuação.
10. Linhas `HUMANO` e estados `BLOQUEADO` do quadro, e faixa que não entregou retro: anote para o relatório; nunca espere.

