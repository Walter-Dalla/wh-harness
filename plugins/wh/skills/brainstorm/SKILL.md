---
name: brainstorm
description: Ideias de produto/design para o repositório atual, ancoradas no estado e no roadmap, numa nota rascunho fora do git.
disable-model-invocation: true
---

# Brainstorm

Perfil do projeto (injetado; `PERFIL_AUSENTE` = `Skill(wh:perfil, "brainstorm")` antes de seguir):
!`cat .claude/perfil/_comum.md .claude/perfil/brainstorm.md 2>/dev/null || echo PERFIL_AUSENTE`

Saída: uma nota rascunho com ideias para o dono decidir, em PT-BR, não código. Código, status de features e `docs/` ficam como estão. Promover uma ideia a trabalho é outro passo (o dono decide; depois o doc de status e `/wh:feature-docs`).

## 1. Enquadrar

Do pedido: **tema** (feature, tensão, fase ou "aberto"), **horizonte** (próximo passo / próxima fase / longo prazo) e restrições dadas (esforço, plataforma, monetização). Sem tema: os itens abertos do roadmap (passo 2). Pergunte só se o tema oscila entre duas áreas muito diferentes; senão declare a premissa na resposta e siga.

## 2. Orientar

Leia na ordem da tabela do perfil § Fontes e pare quando entender a área: títulos primeiro (`grep -n '^#' <arquivo>`), depois só as seções que importam. Orçamento: 6–10 leituras antes de gerar. Docs de regras técnicas (`_comum § Docs`): uma vez, só quando uma ideia depende de uma regra de código. Para saber se algo já existe: `_comum § Navegação` pelo nome, nunca serviço inteiro "para ter contexto". O que o dono disse nesta conversa sobre o futuro vale mais que os docs; diga quando divergem.

**Feito quando você sabe o que existe, o que está planejado e quais decisões já foram tomadas no tema.**

## 3. Divergir

12–20 ideias cruas antes de julgar qualquer uma, girando as lentes do perfil § Lentes para não virem todas do mesmo ângulo.

## 4. Convergir

Fora ou reformulada a ideia que quebra uma restrição do perfil § Restrições; duplicatas fundidas; ficam 5–8. Já existe (passo 2)? Em parte = extensão daquela feature, não feature nova.

## 5. Escrever a nota

Pasta, nome e formato de link: perfil § Nota. Mesmo tema no mesmo dia = atualize a nota existente.

```markdown
---
tags: [brainstorm, rascunho]
status: rascunho
data: AAAA-MM-DD
tema: <tema>
horizonte: <próximo passo | próxima fase | longo prazo>
fontes: [<as que você leu, no formato de link do perfil>]
---

# Brainstorm — <tema>

<Uma linha: tema, horizonte, premissas (e onde o que o dono disse diverge dos docs).>

## Ideias

### <n>. <Nome curto> — <pitch em uma frase, do ponto de vista do usuário>
- **Por quê:** <pilar, tensão ou id que resolve, com link>
- **Como encaixa:** <features tocadas, com link; o que entra e sai; o que o sistema precisa derivar>
- **Esforço:** P/M/G — <camadas tocadas>
- **Riscos / perguntas:** <balanceamento, escala, decisão do dono, informação faltante>
- **Primeiro passo:** <o menor experimento que valida a ideia>

## Priorização
<tabela: ideia × impacto × esforço × dependências, na ordem da sua recomendação>

## Recomendação
<as 1–2 ideias para fazer primeiro e por quê, um parágrafo curto>

## Decisões para o dono
- [ ] <pergunta que só o dono responde> — destrava <ideias>

## Descartadas
- <ideia> — <restrição do passo 4 que ela quebra> (uma linha cada)
```

O que você inferiu sem olhar o código leva *(a verificar)*.

## 6. Relatar

No chat: caminho da nota, a recomendação em duas ou três linhas e as decisões abertas. Confirme que está fora do git (`git check-ignore -v <arquivo>`).
