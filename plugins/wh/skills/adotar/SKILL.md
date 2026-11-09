---
name: adotar
description: Liga o harness wh num repositório que ainda não o tem: diagnostica o que falta, cria CLAUDE.md, perfis, glossário, mapa de features, contexto.json e settings.json, e valida. Use para "adotar o harness", "preparar o projeto para o wh", ou /wh:adotar.
---

# Adotar o harness

Você está na raiz de um repositório que quer usar o plugin `wh`. O plugin já tem os procedimentos; este repo ainda não tem os **fatos** (`.claude/perfil/`) nem as **fontes** do hook (glossário, mapa de features) nem a **declaração** do plugin. Esta skill cria o que falta e valida. Nada de projeto entra no plugin: tudo que você escreve fica no repo.

Argumento: nada (tudo) ou uma lista do que fazer: `checar` (só o diagnóstico), `perfis`, `fontes` (glossário + mapa de features), `hook` (`contexto.json`), `plugin` (`settings.json` + `.gitignore`). Ex.: `/wh:adotar checar`, `/wh:adotar perfis hook`.

Diagnóstico (injetado; roda antes de você ler isto):
!`python3 -I "${CLAUDE_PLUGIN_ROOT}/skills/adotar/scripts/checar.py" --root . 2>&1 || true`

## 1. Diagnosticar

Leia o diagnóstico acima. `FALTA` = esta skill cria; `AVISO` = decisão do dono ou de outra skill (dito no detalhe); `OK` = não toque. Com `checar`: apresente o diagnóstico com uma linha do que cada `FALTA` exigiria e pare.

Confirme a raiz: `git rev-parse --show-toplevel` igual ao cwd. Monorepo: a adoção é por raiz do git, não por pacote; `contexto.json` sobe a árvore a partir do cwd da sessão.

**Feito quando cada linha do diagnóstico está classificada: criar aqui, pedir ao dono, ou deixar.**

## 2. Mapa do repo (`CLAUDE.md`)

`FALTA mapa do repo`: escreva `CLAUDE.md` na raiz, ≤ 30 linhas, só ponteiros de navegação: o que o projeto é (uma linha), onde cada camada mora (pastas), como construir e testar (os comandos que o `README`, CI e scripts de build mostram), quais docs ler e quando. Fontes: `README`, `.github/workflows/*`, `package.json`/`pyproject.toml`/`*.sln`/`Makefile`, árvore do repo (`ls`, 2 níveis). Nenhuma regra de estilo aqui: regra mora em doc apontado. `AGENTS.md` já existe = não crie `CLAUDE.md`; a skill `perfil` lê os dois.

**Feito quando o mapa existe e cada caminho citado nele existe.**

## 3. Perfis

`Skill(wh:perfil)` sem argumento: escreve `_comum.md`, `implementation.md` e os perfis das skills cuja fonte existe no repo. Dono presente: a skill `perfil` confirma as linhas `[inferido]`; sessão sem dono (`-p`, subagente): `Skill(wh:perfil, "adiar")` e liste as linhas no relatório final. Depois, `Read` dos arquivos escritos.

`AVISO skill antiga` (pasta `.claude/skills/<skill>` com o mesmo nome de uma skill do plugin): a skill `perfil` leva os fatos para o perfil e remove a pasta (§ 4 dela). Confira que removeu.

**Feito quando `.claude/perfil/_comum.md` e `implementation.md` existem com toda seção do modelo e o diagnóstico (§ 6) não acusa `FALTA perfil`.**

## 4. Fontes do hook

Só quando o repo tem domínio para isso (entidades, serviços, telas com nome de negócio). Biblioteca pequena ou script sem vocabulário próprio: pule e diga que pulou.

- **Glossário** (`FALTA glossario`): crie `docs/GLOSSARIO.md`: seções `##` por área, cada uma com a tabela `| Negócio | Código | Evite / nota |` (Código entre crases; Evite entre aspas duplas), e `## Armadilhas` com `| No código | Significa | Por quê |`. Semeie com os termos que o código mostra sem ambiguidade: nome de entidade, serviço, rota, enum (`codegraph explore` se `.codegraph/` existe; senão a árvore e os arquivos de modelo). Coluna Negócio: o nome que o `README`/docs usam; sem nome de negócio, o próprio identificador. Coluna Evite: só sinônimos que o repo de fato confunde (docs, issues, commits); nada inventado. 10 a 30 linhas; o dono completa.
- **Mapa de features** (`FALTA features`/`indice_features`): crie `docs/features/README.md` com a tabela `| Arquivo | Feature | Procure aqui quando a tarefa fala de… |` (link na primeira célula; as outras viram palavras-chave separadas por vírgula) e um arquivo por feature candidata: módulo ou pasta com loop próprio para o usuário e dono próprio no código (serviço/entidade/endpoints ou painel). Cada arquivo: frontmatter `aliases`, `# Título`, uma linha de resumo, `## Símbolos de entrada` (identificadores entre crases, lidos do código), `## Interações` (links `[x](x.md)` só para dependências que o código mostra). ≤ 20 linhas cada: o `/wh:feature-docs` engorda depois, quando tiver perfil. Mais de 8 candidatas: crie as 8 mais centrais e liste o resto no índice sem arquivo (uma linha com `—` na coluna Arquivo).
- Idioma: o das docs do repo. Em inglês, nomes de seção `Entry symbols`, `Interactions`, `Pitfalls` (o hook aceita os dois) e `"idioma": "en"` no `contexto.json`.

**Feito quando o glossário e o índice parseiam: `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/prompt_graph.py" --build --root .` mostra termos e features > 0 (precisa do `contexto.json` da § 5).**

## 5. `contexto.json`, `settings.json`, `.gitignore`

- `FALTA contexto.json`: escreva `.claude/perfil/contexto.json` com só as chaves cujo valor difere do padrão (`glossario`, `features`, `indice_features`, `codegraph`, `idioma`; padrões e demais chaves em `DEFAULTS` de `${CLAUDE_PLUGIN_ROOT}/scripts/prompt_graph.py`). Sem glossário nem features (pulou a § 4): não crie o arquivo e diga "hook desligado: sem fontes".
- `FALTA settings.json`: crie ou complete `.claude/settings.json` (merge: nunca apague chaves existentes) com `extraKnownMarketplaces.wh-harness` (`source: github`, `repo: Walter-Dalla/wh-harness`) e `enabledPlugins."wh@wh-harness": true`. Fixar versão (`"ref": "<tag>"`) só se o dono pediu.
- `.gitignore`: acrescente `.codegraph/` se não está. `.impl/` fica no `.git/info/exclude` (o `/wh:implementation` faz); não o ponha no `.gitignore`.
- `AVISO codegraph` com CLI presente e índice ausente: **não rode** `codegraph init`; indexar é decisão do dono. Entra no relatório como pendência com o comando.

**Feito quando os três arquivos existem e `python3 -m json.tool` aceita os dois JSON.**

## 6. Validar

1. Rode de novo `python3 -I "${CLAUDE_PLUGIN_ROOT}/skills/adotar/scripts/checar.py" --root .`: zero `FALTA` (fora as que o dono decidiu deixar, ditas no relatório).
2. Hook: `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/prompt_graph.py" --query "<frase com 2 termos do glossário>" --root . --explain`: a feature certa aparece em "Ler". Não aparece: acrescente a palavra na linha do índice ou nos `aliases`.
3. Cada caminho citado em `CLAUDE.md`, nos perfis (`_comum § Docs`) e no `contexto.json` existe (`ls`).

**Feito quando os três passam.**

## 7. Relatar

Em ordem: arquivos criados e alterados (um por linha); o que ficou `AVISO` e quem resolve (dono: `codegraph init -y .`, linhas `[inferido]`, perfis opcionais; outra skill: `/wh:feature-docs` para engordar o mapa); o que foi pulado e por quê; e os dois passos finais que só o dono faz: commitar `.claude/perfil/`, `.claude/settings.json`, `CLAUDE.md`, `docs/` e abrir uma sessão nova (hooks e plugins carregam no início da sessão). Commit só se o dono pedir.
