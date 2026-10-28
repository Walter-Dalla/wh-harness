---
name: perfil
description: Gera ou completa o perfil de projeto de uma skill (`.claude/perfil/_comum.md` e `.claude/perfil/<skill>.md`) a partir do PERFIL.md da skill. Chamada por outra skill quando o perfil falta ou tem seção a menos, ou pelo dono com `/wh:perfil <skill>`.
---

# Perfil de projeto

Argumento: o nome da skill (`start-app`, `deploy`, `implementation`…). Sem argumento: todas as skills de `${CLAUDE_PLUGIN_ROOT}/skills/*/PERFIL.md`.

Um **perfil** é o que uma skill genérica precisa saber do repositório e não descobre sozinha: comandos, caminhos, portas, docs, limites. Só fatos, cada um com a fonte entre colchetes; o procedimento fica na skill. Dois arquivos, versionados no repo, lidos só pela skill (nunca carregam sozinhos):

| Arquivo | Modelo | Conteúdo |
|---|---|---|
| `.claude/perfil/_comum.md` | [`COMUM.md`](COMUM.md) | o que toda skill usa: clone, toolchain, git, portas, navegação, docs, limites |
| `.claude/perfil/<skill>.md` | `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/PERFIL.md` | só o que aquela skill usa; cita `_comum § X` em vez de repetir |

## 1. Diferença

Leia o modelo e o arquivo atual (se existir). A diferença é a lista de seções `##` do modelo que faltam no arquivo. Seção a mais no arquivo fica (conhecimento do repo). Arquivo completo = diga isso e pare.

**Feito quando toda seção do modelo está classificada: presente ou faltando.**

## 2. Fontes

Para cada seção faltando, nesta ordem, parando na primeira que responde: `CLAUDE.md`/`AGENTS.md` e os docs que eles apontam; `.claude/perfil/*.md` já escritos; a skill antiga do projeto em `.claude/skills/<skill>/SKILL.md` (migração: os fatos dela vêm para o perfil); workflows de CI (`.github/workflows/*`); scripts de build e dev (`package.json`, `Makefile`, `*.sln`, `pyproject.toml`, `scripts/`, `deploy/`); `README`. Cada linha do perfil termina com a fonte: `[CLAUDE.md]`, `[ci: tests.yml]`, `[scripts/dev.sh]`, `[skill antiga]`, `[inferido]`. Repo sem resposta: a seção fica `—` (a skill pula a fase que depende dela e diz que pulou).

**Feito quando toda seção faltando tem texto com fonte ou `—`.**

## 3. Confirmar

Linhas `[inferido]` vão numa só `AskUserQuestion` para o dono. Sessão sem dono (subagente, `--autonomo`): ficam marcadas `[inferido]` e a resposta final as lista.

## 4. Escrever

Fatos, uma linha por fato, comandos entre crases e completos (com `<porta>`, `<slug>`, `<filtro>` onde a skill substitui). Nada que o `_comum.md` já diz: cite `_comum § Git`. Nada de procedimento ("primeiro faça X, depois Y"): isso é da skill. Alvo: `_comum.md` ≤ 40 linhas, `<skill>.md` ≤ 60; passou, o excesso vira um doc do repo apontado pelo perfil.

Migração de skill antiga do projeto: depois que o perfil tem os fatos dela, `git rm -r .claude/skills/<skill>` (nome igual no projeto sombreia a skill do usuário). Scripts e harness que a skill antiga carregava vão para uma pasta do repo (`deploy/`, `tools/`, `scripts/`) e o perfil aponta para lá.

**Feito quando `.claude/perfil/_comum.md` e `.claude/perfil/<skill>.md` têm toda seção do modelo, toda linha com fonte, e a skill antiga do projeto (se havia) saiu.**

## 5. Responder

Seções escritas, seções `—`, linhas `[inferido]` não confirmadas. Commit só se o dono pedir ou se a skill chamadora manda (o `/wh:implementation` commita o perfil na branch da tarefa).
