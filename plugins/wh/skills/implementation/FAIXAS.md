# Tarefa grande: faixas paralelas `impl-dev`

Cada faixa = um subagente `impl-dev` na própria worktree e na própria branch (`impl/<slug>-<faixa>`, no remote a cada commit). Você escreve as faixas, dispara, une e valida; código você escreve só no conserto de merge.

## 1. Dividir em faixas (o enriquecedor faz, na etapa `planejar`)

O equilíbrio é **paralelismo × reuso de contexto × tokens**:

- **Mesmo lugar, mesmo desenvolvedor.** Itens no mesmo arquivo, no mesmo invariante, no mesmo contrato ou no mesmo módulo vão numa faixa, em ordem de dependência: o segundo item reaproveita o que o primeiro já leu. Refactor vai na mesma faixa (e antes) da feature que mexe no mesmo código.
- **Paralelo só no que não se toca.** Faixas da mesma onda são donas de arquivos disjuntos. Arquivos de união (perfil § Arquivos de união) podem ser de várias: cada faixa só acrescenta, você resolve no merge.
- **Contrato em ondas.** A faixa produtora dona do contrato numa onda; o consumidor numa onda seguinte.
- **Tamanho.** Estime cada faixa: ~70k fixos (instruções, ferramentas, índice) + por item ~25k (interno, um ou dois arquivos) a ~60k (contrato ou vários arquivos), + a suíte do fim.
- **Limite.** No máximo 3 subagentes vivos (`SKILL.md` § Limite de subagentes); com o enriquecedor vivo, uma onda tem no máximo 2 faixas em paralelo: onda maior vira ondas menores, ou as faixas extras esperam vaga.
  - **Teto:** a janela é de 1M; mire em ≤ ~400k por faixa, onde a qualidade se mantém. Acima disso, parta a faixa pelo ponto de menor acoplamento (itens em série viram duas faixas em ondas seguidas).
  - **Piso:** faixa com menos de ~3 itens ou ~150k estimados é pequena demais (paga os 70k fixos por pouco trabalho): junte à vizinha com quem divide arquivos, ou ponha o item na onda seguinte de outra faixa.
- **Largura:** no máximo 4 faixas ao mesmo tempo (CPU da máquina: builds e testes); uma porta do perfil por faixa.

Uma faixa = `<raiz>/.impl/<slug>/<faixa>.md`; o agente não vê esta conversa, então tudo o que ele precisa está aqui. Os caminhos de `Dono de:`, `Pode tocar` e `União:` vão entre crases: o `scripts/escopo.sh` os lê (`União:` copia o perfil § Arquivos de união).

```markdown
# <faixa> · <slug> · onda W<n> · porta <do perfil ou —> · ~<k> tokens estimados
Contexto: <o pedido enriquecido e as decisões que tocam esta faixa>.
Dono de: `<caminho ou glob>` `<…>` (símbolos à parte). Pode tocar o mínimo de: `<caminho de outra faixa>` (ou "—"). União: `<glob>` `<…>` (ou "—").
Par: <faixa que consome ou fornece contrato, ou "—">.
## <id> · <título> · interno|contrato
<o que mudar, símbolos e arquivo:linha do enriquecimento, regra que vale>. Aceite: `<comando>`.
```

No `PLANO.md`, acrescente a tabela `| Onda | Faixa | Itens | Porta | Estimativa |`. Crie `<raiz>/.impl/<slug>/QUADRO.md` vazio e a pasta `retros/`.

## 2. Disparar

Commit e push da `impl/<slug>` antes da primeira onda (é a base). Antes de cada onda, a base é a ponta real da `impl/<slug>` (`git rev-parse impl/<slug>`), com a onda anterior inteira mergeada e verde; anote no quadro `orquestrador | ONDA | W<n> base <hash>`. Dispare respeitando o limite de 3 subagentes vivos (`SKILL.md` § Limite de subagentes): a próxima faixa ou QA só quando um agente terminou. Prompt de cada agente:

```text
Faixa: <faixa>. Arquivo: <raiz>/.impl/<slug>/<faixa>.md. Repo: <raiz>. Perfil: <raiz>/.claude/perfil/implementation.md e _comum.md.
Branch: impl/<slug>-<faixa>. Base: impl/<slug> @ <hash>. Remote: <remote>.
Porta: <porta ou —>. Quadro: <raiz>/.impl/<slug>/QUADRO.md.
Retro: .impl/<slug>/retros/<faixa>.md (relativo à sua worktree).
Continuação: <"do zero" | PROGRESS.md anterior + branch de onde seguir + o que mudou na base ou na faixa desde então>.
```

`Agent(subagent_type: "wh:impl-dev", isolation: "worktree", model: "opus", prompt: …)`, **sem `name`** (com nome vira colega de agent team). Guarde o id de agente de cada faixa (consertos e respostas voltam a ele). Enquanto rodam, espere os relatórios; os diffs você lê no merge.

**Ponte de dúvidas:** mensagem `PERGUNTA …` de uma faixa = consulta ao enriquecedor (fase 2 do `SKILL.md`, "Consultas durante a tarefa"), resposta ao id da faixa. Relatório `AGUARDANDO: …` = a mesma consulta; a resposta retoma a faixa.

## 3. QA de código, unir e validar (por faixa, na ordem da onda)

1. **Estado e escopo:** relatório `CONCLUIDO` com evidência por item (senão, `PARCIAL`/`BLOQUEADO`: passo 9); `${CLAUDE_PLUGIN_ROOT}/skills/implementation/scripts/escopo.sh <faixa.md> <base> <remote>/impl/<slug>-<faixa>` sem `FORA:` (senão a faixa conserta, `SendMessage`).
2. **QA de código** (fase 4 do `SKILL.md`) logo que a faixa entrega: `impl-qa` modo `codigo` na `impl/<slug>-<faixa>`, base = o hash de onde a faixa partiu. Roda enquanto as outras faixas da onda ainda trabalham.
3. **Consertos da faixa:** os achados de bug, padrão ou nome voltam ao **mesmo** `impl-dev` (`SendMessage` com o id do agente devolvido no spawn: ele retoma com o contexto da faixa), com a lista de ids e o arquivo do QA; ele faz um commit por achado e push. Depois, o reteste pela regra da fase 4 do `SKILL.md` (agente só com achado de código crítico, alto ou médio).
4. **Arquivos da faixa:** copie a retro (e a saída do QA) da worktree para `<raiz>/.impl/<slug>/` (`SKILL.md` § Arquivos de subagente em worktree).
5. **Merge:** `git fetch <remote>` e `git merge --no-ff <remote>/impl/<slug>-<faixa> -m "impl: <faixa>"` na `impl/<slug>`; anote no quadro `orquestrador | MERGE | <faixa> → <hash>`.
6. **Conflito:** resolva mantendo a intenção das duas faixas (a do relatório de cada uma); arquivo de união = as duas listas de linhas. Conflito que exige reescrever lógica: aborte o merge e mande a faixa que entrou depois (`SendMessage`) fazer "rebase em impl/<slug> e resolva <arquivos>".
7. **Revisão rápida:** `git diff --stat`; nenhuma fixture de contrato recebida ou lixo de teste. Fixture tocada por duas faixas da onda: a segunda roda de novo pelo perfil § Contrato na integração e você revisa o diff.
8. **Fim de onda:** build e suíte do perfil na ponta da `impl/<slug>`, depois push. Doc protegido (perfil § Arquivos protegidos) que a onda deixou desatualizado, você corrige aqui com as notas das faixas, em commit próprio. Checks caros e QA visual/e2e ficam para o QA final (fase 5). Verde: próxima onda (a base nova é esse hash). Vermelho: conserto de uma linha você faz em commit próprio (`<slug>-fix: …`); senão a faixa culpada conserta (`SendMessage`).
9. **Faixa parcial ou bloqueada:** `BLOQUEADO` = resolva o ambiente; depois, agente novo com o mesmo prompt + o `PROGRESS.md` dela (checkpoint), base = ponta da branch dela, e o que mudou desde então; o QA de código roda depois da continuação.
10. Linhas `HUMANO` e estados `BLOQUEADO` do quadro, e faixa que não entregou retro: anote para o relatório; nunca espere.

Fim de todas as ondas: `git worktree remove` das worktrees mergeadas (as branches ficam no remote até o PR).
