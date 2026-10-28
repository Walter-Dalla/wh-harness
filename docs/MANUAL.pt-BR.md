# Manual técnico — harness de implementação em um projeto novo

Este manual descreve como o ambiente de implementação funciona e como ligá-lo em um repositório que ainda não tem nada dele. O ambiente tem duas metades:

- **Genérica**, no plugin `wh` (repo `wh-harness`, instalado no usuário): procedimentos das skills, agentes e hooks. Vale para todo projeto e nunca cita um comando de projeto.
- **Do projeto**, versionada no repo (`.claude/perfil/`): os fatos que a metade genérica não descobre sozinha (comandos, portas, docs, limites, fontes do glossário e do mapa de features).

A regra que segura as duas metades: **a skill tem o procedimento, o perfil tem os fatos.** A skill cita uma seção do perfil (`perfil § Testes`), nunca um comando.

---

## 1. Peças e onde moram

| Peça | Caminho | Papel |
|---|---|---|
| Plugin `wh` | `plugins/wh/` (marketplace `wh-harness`) | tudo o que é genérico; comandos `/wh:<skill>`, agentes `wh:<agente>` |
| Skills genéricas | `plugins/wh/skills/<skill>/SKILL.md` | procedimento (`implementation`, `limpeza`, `deploy`, `start-app`, `qa-visual`, `feature-docs`, `brainstorm`, `perfil`) |
| Modelo do perfil da skill | `plugins/wh/skills/<skill>/PERFIL.md` | quais seções `##` o perfil daquela skill precisa ter |
| Modelo do perfil comum | `plugins/wh/skills/perfil/COMUM.md` | seções que toda skill usa |
| Gerador de perfil | `plugins/wh/skills/perfil/SKILL.md` (`/wh:perfil <skill>`) | escreve ou completa os perfis a partir dos modelos e do repo |
| Agentes | `plugins/wh/agents/impl-enrich.md`, `impl-dev.md`, `impl-qa.md` | subagentes do `/wh:implementation` (`subagent_type: "wh:impl-dev"`…) |
| Hooks | `plugins/wh/hooks/hooks.json`, `plugins/wh/scripts/` | hooks determinísticos; hoje o `prompt-graph` |
| Perfil comum do projeto | `<repo>/.claude/perfil/_comum.md` | clone, toolchain, git, portas, navegação, docs, limites |
| Perfil de cada skill | `<repo>/.claude/perfil/<skill>.md` | só o que aquela skill usa; cita `_comum § X` em vez de repetir |
| Fontes do hook | `<repo>/.claude/perfil/contexto.json` | liga o `prompt-graph` no projeto e diz onde estão glossário, features e CodeGraph |
| Declaração do plugin no projeto | `<repo>/.claude/settings.json` | faz quem clona o projeto receber o plugin (§4) |
| Cache do grafo | `~/.cache/walter-harness/<hash do caminho do repo>.json` (ou `$WH_CACHE_DIR`) | gerado; nunca versionar |

---

## 2. Mecanismo 1 — injeção do perfil nas skills

Cada skill genérica começa com um comando de pré-processamento do Claude Code, que roda **antes** de o modelo ler a skill e cola a saída no texto dela:

```markdown
Perfil do projeto (injetado; `PERFIL_AUSENTE` = fase 1 escreve o perfil antes de seguir):
!`cat .claude/perfil/_comum.md .claude/perfil/implementation.md 2>/dev/null || echo PERFIL_AUSENTE`
```

Fluxo:

1. O usuário chama `/wh:implementation …` na raiz do repo.
2. O `cat` roda no diretório da sessão. Se os perfis existem, o conteúdo deles entra na skill; se não, entra a palavra `PERFIL_AUSENTE`.
3. Com `PERFIL_AUSENTE` ou com seção faltando, a skill chama `Skill(wh:perfil, "<skill>")` antes de seguir.
4. A skill `perfil` compara o arquivo com o modelo (`PERFIL.md` ou `COMUM.md`), procura cada seção faltante nas fontes do repo (em ordem: `CLAUDE.md`/`AGENTS.md` e docs apontados, perfis já escritos, skill antiga do projeto, `.github/workflows/*`, scripts de build, `README`) e escreve uma linha por fato com a fonte entre colchetes (`[ci: tests.yml]`, `[inferido]`…). Linhas `[inferido]` vão para o dono em uma única pergunta. Seção sem resposta fica `—`, e a skill pula a fase que depende dela, avisando que pulou.

Os caminhos para arquivos do próprio plugin (modelos, scripts, a retro) são escritos como `${CLAUDE_PLUGIN_ROOT}/skills/…`; o Claude Code troca a variável pelo caminho real ao carregar a skill (testado; `${CLAUDE_SKILL_DIR}` também funciona). Os agentes não recebem a variável resolvida: o `/wh:implementation` passa `PLUGIN_ROOT=<caminho>` no prompt de cada subagente.

Consequências práticas:

- **O perfil é lido só pela skill.** Ele não carrega sozinho na sessão; por isso pode ser denso e factual.
- **Tamanho alvo:** `_comum.md` ≤ 40 linhas, `<skill>.md` ≤ 60. O excesso vira um doc do repo apontado pelo perfil.
- **Sem sombreamento:** as skills do plugin têm prefixo (`/wh:implementation`), então uma skill do projeto com o nome curto (`<repo>/.claude/skills/implementation/`) convive com ela, mas confunde. Na migração de um projeto que já tinha skills próprias, os fatos delas vão para o perfil e a pasta antiga sai (`git rm -r .claude/skills/<skill>`).
- **Worktrees:** o perfil é versionado, então toda worktree de agente já nasce com ele.

---

## 3. Mecanismo 2 — hook `prompt-graph` (enriquecimento do prompt)

### 3.1 O que faz

A cada prompt enviado, o Claude Code roda o hook `UserPromptSubmit` do plugin `wh`:

```
python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/prompt_graph.py"     (timeout 5 s)
```

O script recebe o evento em JSON pelo stdin (`prompt`, `cwd`), casa o texto contra um grafo do domínio e devolve `hookSpecificOutput.additionalContext`. Esse texto entra no contexto do modelo junto com o prompt. Não há LLM, rede nem aleatoriedade: o mesmo prompt com as mesmas fontes produz sempre a mesma saída.

Exemplo de saída:

```
[wh:prompt-graph] Contexto determinístico (glossário + features + CodeGraph); só ponteiros, confira antes de afirmar.
Evite "vitrine": o termo é Balcão (`Counter`)
Termos: Balcão = `Counter` · Porção = portion (`Portions`)
Ler: docs/features/balcoes.md (Balcões e pratos preferidos) · docs/features/cozinha.md (Cozinha e cardápio)
Interage com: tudo-pronto, fregueses, despensa, clientes, reputacao, decorar
Símbolos: CounterService KittyCaffeeBackend/Src/Services/CounterService.cs:48 · Counter …/Counter.cs:3
```

A saída tem só ponteiros e um teto de `max_chars`. O modelo decide o que abrir. Prompt sem termo do domínio não injeta nada.

### 3.2 Quando fica em silêncio

- Não há `.claude/perfil/contexto.json` subindo a árvore a partir do `cwd` (projetos sem o arquivo nunca são afetados).
- O prompt tem menos que `min_prompt` caracteres.
- Nenhuma feature passa de `min_score` e nenhum termo casou.
- A variável `WH_PROMPT_GRAPH=0` está no ambiente da sessão.
- Qualquer exceção: o erro vai para o stderr e o prompt segue normalmente. O hook nunca bloqueia.

### 3.3 O grafo

**Nós**

- **Termo**: cada linha das tabelas do glossário.
- **Feature**: cada `<features>/*.md`, menos o `README.md`.
- **Símbolo**: identificadores citados em `## Símbolos de entrada` das features e na coluna Código do glossário.

**Chaves de busca (alias → nó, com peso)**

| Origem | Aponta para | Peso |
|---|---|---|
| Palavras-chave da linha da feature no índice (`README.md`) | feature | 3 |
| `aliases:` do frontmatter e `# Título` da feature | feature | 3 |
| Identificador em `## Símbolos de entrada` | feature | 2 |
| Coluna Negócio do glossário (partes separadas por `/` e `,`, sem parênteses) | termo | — |
| Identificadores entre crases na coluna Código | termo | — |
| Palavras entre aspas na coluna Evite | termo, como aviso "Evite" | — |

**Arestas**

- **Termo → feature:** quando alguma chave do termo aparece no corpo do arquivo da feature. Peso 1, dividido entre as features ligadas.
- **Feature → feature:** links `[x](x.md)` da seção `## Interações`. Viram a linha "Interage com" da feature de maior pontuação.
- **Símbolo → `arquivo:linha`:** consulta somente leitura ao SQLite do CodeGraph (`nodes.name`). Quando o mesmo nome aparece mais de uma vez, vence o que tem melhor tipo (classe, depois interface, rota, método…), fora de pasta de teste e com caminho mais curto. Os globs de `class_name_globs` resolvem `class_name X` de scripts Godot, que não estão no índice.

**Regra do Evite:** um sinônimo entre aspas só vira aviso quando não é termo próprio de outra linha. Exemplo: "nível" é evitado em "Tier", mas é o termo Nível, então não gera aviso.

### 3.4 Consulta (por prompt)

1. **Normalização** (igual para prompt e chaves): NFKD sem acento, minúsculas, tokens `[a-z0-9_]+` e um radical simples de plural PT-BR (`-ões`/`-ães` → `-ão`, `-ais` → `-al`, `-eis` → `-el`, `-ns` → `-m`, `-s` final). Identificadores viram um token só (`CounterService` → `counterservice`).
2. **Casamento guloso por n-grama**, do mais longo (5 tokens) ao mais curto. Um token já usado não entra em casamento menor.
3. **Pontuação:** cada chave casada soma `peso / nº de features que ela aponta` em cada feature. Cada termo casado soma 1 dividido entre as features ligadas a ele.
4. **Saída:**
   - avisos Evite (até 2);
   - termos (até `max_termos`);
   - features com pontuação ≥ `min_score` (até `max_features`);
   - vizinhos da primeira feature (até `max_interage`);
   - símbolos (até `max_simbolos`): primeiro os citados no prompt, depois os de entrada das features, alternando entre elas.

### 3.5 Cache e desempenho

- **Assinatura do cache:** SHA-1 de versão do grafo, mtime do script e mtime e tamanho de `contexto.json`, do glossário, de cada feature e do `codegraph.db`. Qualquer mudança refaz o grafo no próximo prompt.
- **Gravação:** atômica (arquivo `.tmp` seguido de `os.replace`), segura com várias sessões ao mesmo tempo.
- **Tempos medidos no KittyCaffee** (29 features, 240 termos, 334 símbolos, ~1060 chaves): reconstrução ~0,18 s; consulta com cache quente ~30 ms.
- **Custo de contexto:** cerca de 300 a 900 caracteres por prompt com acerto e zero sem acerto.

---

## 4. Ligando um projeto novo — passo a passo

Duas formas de ter o plugin:

- **Consumidor** (qualquer pessoa, qualquer máquina): pelo GitHub.

  ```bash
  claude plugin marketplace add Walter-Dalla/wh-harness
  claude plugin install wh@wh-harness
  ```

- **Mantenedor** (quem edita o harness): pelo diretório. O Claude Code lê o plugin direto da pasta, então uma edição vale na sessão seguinte, sem push.

  ```bash
  git clone https://github.com/Walter-Dalla/wh-harness ~/walter-harness
  claude plugin marketplace add ~/walter-harness
  claude plugin install wh@wh-harness
  claude plugin list | grep -A4 'wh@'            # Status: ✔ enabled
  ```

No projeto novo:

1. **Mapa do repo.** Tenha um `CLAUDE.md` (ou `AGENTS.md`) na raiz que diga onde cada coisa mora e quais docs ler. Ele é a primeira fonte da skill `perfil`.
2. **Perfil comum e das skills.** Na raiz do repo, rode `/wh:perfil` (todas as skills) ou `/wh:perfil implementation` (uma só). Revise `.claude/perfil/_comum.md` e `.claude/perfil/<skill>.md`, responda às linhas `[inferido]` e confira se `## Limites` diz o que nenhum agente toca (produção, segredos, banco do dono).
3. **Glossário** (opcional, mas é o que alimenta o hook). Crie `docs/GLOSSARIO.md` no formato da §5.1.
4. **Mapa de features** (opcional). Crie `docs/features/README.md` e um arquivo por feature no formato da §5.2. A skill `/wh:feature-docs` mantém esse mapa depois que o perfil dela existir.
5. **CodeGraph** (opcional). `codegraph init -y .` na raiz cria `.codegraph/`. Coloque `.codegraph/` no `.gitignore`.
6. **Ligue o hook** criando `.claude/perfil/contexto.json`:

   ```json
   {
     "glossario": "docs/GLOSSARIO.md",
     "features": "docs/features",
     "indice_features": "docs/features/README.md",
     "codegraph": ".codegraph/codegraph.db",
     "class_name_globs": []
   }
   ```

   Caminhos relativos à raiz do repo. Fonte ausente não quebra nada: sem glossário não há termos; sem CodeGraph os símbolos saem sem `arquivo:linha` e não aparecem na linha "Símbolos".
7. **Declare o plugin no projeto** em `.claude/settings.json`, para que quem clonar receba a oferta de instalar ao confiar na pasta:

   ```json
   {
     "extraKnownMarketplaces": {
       "wh-harness": { "source": { "source": "github", "repo": "Walter-Dalla/wh-harness" } }
     },
     "enabledPlugins": { "wh@wh-harness": true }
   }
   ```

   Para fixar uma versão, acrescente `"ref": "v0.2.0"` ao `source`. Sem `ref`, o projeto acompanha o `main`.
8. **Valide** antes de abrir sessão (ver §6). Depois, commite `.claude/perfil/` e `.claude/settings.json`.
9. **Abra uma sessão nova.** Hooks e plugins carregam no início da sessão.

---

## 5. Formato das fontes

O parser é por convenção de markdown. Fora do formato, a linha é ignorada sem erro.

### 5.1 Glossário

```markdown
## <Seção qualquer>

| Negócio | Código | Evite / nota |
|---|---|---|
| Balcão | `Counter` | "vitrine" |
| Mesa / cadeira | `Table` / `Chair` | |
| Cliente (cliente anônimo) | NPC: `ActiveNpc`, `Npc` | "freguês" para o anônimo |

## Armadilhas

| No código | Significa | Por quê |
|---|---|---|
| `Entrace` | entrada / porta | typo histórico |
```

- **Negócio:** partes separadas por `/` ou `,` viram chaves. O texto entre parênteses é descrição e não vira chave. Partes com menos de 3 caracteres são descartadas.
- **Código:** só o que está entre crases e parece identificador (`Nome`, `a.b`) ou rota (`GET /x`, `POST /x`).
- **Evite:** só o que está entre aspas duplas (3 a 40 caracteres).
- Na seção `## Armadilhas` as colunas são lidas na ordem código, significado e motivo.

### 5.2 Mapa de features

`docs/features/README.md`: uma linha de tabela por feature, com o link na primeira célula. As outras células viram palavras-chave, separadas por vírgula (vírgula dentro de crase não separa):

```markdown
| Arquivo | Feature | Procure aqui quando a tarefa fala de… |
|---|---|---|
| [balcoes.md](balcoes.md) | Balcões (F-04) | balcão, porção, `CounterService`, `counter_empty` |
```

`docs/features/<feature>.md`:

```markdown
---
aliases: [Balcões, Pratos preferidos, F-04]
---

# Balcões e pratos preferidos (F-04)

## Símbolos de entrada

Backend: `CounterService`, `Counter`, `CounterDto`.
Cliente: `KitchenStore`.

## Interações

- **Cozinha** ([cozinha.md](cozinha.md)): …
```

Seções lidas: frontmatter `aliases`, `# Título`, `## Símbolos de entrada` (só identificadores entre crases) e `## Interações` (só links `[...](x.md)`). O resto do corpo serve apenas para ligar termos do glossário à feature.

### 5.3 `contexto.json`, todas as chaves

| Chave | Padrão | Efeito |
|---|---|---|
| `glossario` | `docs/GLOSSARIO.md` | arquivo do glossário |
| `features` | `docs/features` | pasta das features |
| `indice_features` | `docs/features/README.md` | índice com palavras-chave |
| `codegraph` | `.codegraph/codegraph.db` | SQLite do CodeGraph (aberto só para leitura) |
| `class_name_globs` | `[]` | globs (com `**`) de scripts com `class_name X` |
| `max_features` | `3` | features em "Ler" |
| `max_termos` | `4` | termos em "Termos" |
| `max_simbolos` | `5` | símbolos em "Símbolos" |
| `max_interage` | `6` | vizinhos em "Interage com" |
| `min_score` | `1.2` | pontuação mínima para uma feature aparecer |
| `min_prompt` | `12` | prompts menores são ignorados |
| `max_chars` | `900` | teto do texto injetado |
| `idioma` | `pt` | rótulos da saída: `pt` ou `en` |
| `secoes` | PT e EN | nomes de seção aceitos, ex.: `{"simbolos": ["Entry symbols"], "interacoes": ["Interactions"], "armadilhas": ["Pitfalls"]}` |

---

## 6. Validação e depuração

```bash
H=~/walter-harness/plugins/wh/scripts/prompt_graph.py   # no clone do harness

# Testes do próprio harness (stdlib, sem dependências)
python3 -m unittest discover -s ~/walter-harness/tests

# Reconstrói e mostra o tamanho do grafo
python3 -I $H --build --root .
# grafo: 1059 chaves, 29 features, 240 termos, 334 símbolos

# Simula um prompt; --explain mostra no stderr as chaves casadas e o ranking
python3 -I $H --query "o balcão não recebe porções" --root . --explain

# Simula o evento real do hook
echo '{"prompt":"o balcão não recebe porções","cwd":"'$PWD'"}' | python3 -I $H
```

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Nada é injetado em nenhum prompt | sem `contexto.json`, plugin desativado ou sessão antiga | `claude plugin list`; abra uma sessão nova |
| A feature certa não aparece | palavra do prompt ausente das palavras-chave | `--explain`; acrescente a palavra no índice ou nos `aliases` da feature |
| Muitas features empatadas | palavra genérica em muitas linhas | tire a palavra do índice ou suba `min_score` |
| Símbolo sem `arquivo:linha` | fora do CodeGraph | `codegraph sync .` ou `class_name_globs` |
| Símbolo aponta para o lugar errado | nome repetido no índice | use o nome mais específico em `## Símbolos de entrada` |
| Aviso "Evite" falso | palavra entre aspas também é termo usado | o filtro já cobre termos próprios; senão, tire as aspas |
| Grafo velho | não deveria acontecer (assinatura por mtime) | `--build`, ou apague `~/.cache/walter-harness/*.json` |

Para desligar só numa sessão: `WH_PROMPT_GRAPH=0 claude`. Para desligar no projeto: remova o `contexto.json`. Para desligar em tudo: `claude plugin disable wh@wh-harness`. O CodeGraph é aberto só para leitura (`mode=ro`); com o índice sendo gravado ao mesmo tempo, a consulta espera até 1 s e segue sem símbolos.

---

## 7. Estendendo

**Nova skill genérica**

1. Crie `plugins/wh/skills/<nome>/SKILL.md` com o procedimento e, no topo, a injeção:

   ```markdown
   !`cat .claude/perfil/_comum.md .claude/perfil/<nome>.md 2>/dev/null || echo PERFIL_AUSENTE`
   ```

2. Crie `plugins/wh/skills/<nome>/PERFIL.md` com o modelo das seções `##` de que a skill precisa.
3. No corpo da skill, cite `perfil § <Seção>`, nunca um comando. Trate `PERFIL_AUSENTE` chamando `Skill(wh:perfil, "<nome>")`. Arquivos do plugin: `${CLAUDE_PLUGIN_ROOT}/skills/<nome>/…`.
4. Suba `version` em `plugins/wh/.claude-plugin/plugin.json` e crie a tag `v<versão>`.

**Novo hook genérico:** script em `plugins/wh/scripts/` e uma entrada em `plugins/wh/hooks/hooks.json` usando `${CLAUDE_PLUGIN_ROOT}`. O que depender do projeto vem de um arquivo em `.claude/perfil/`; sem esse arquivo, o hook sai em silêncio. Um hook nunca bloqueia: exceção vai para o stderr. Teste em `tests/` contra `examples/demo/`.

**Novo agente:** `plugins/wh/agents/<nome>.md`; quem o chama usa `subagent_type: "wh:<nome>"` e passa `PLUGIN_ROOT` no prompt.

## 8. Limites conhecidos

- **Casamento léxico, não semântico.** "Freguês irritado" casa "freguês", mas uma paráfrase sem nenhuma palavra do glossário ou do índice não casa nada. A qualidade depende das palavras-chave do índice.
- **Radical de plural simplificado.** Formas irregulares (`pães`, `colheres`) podem não casar com o singular.
- **Termo com nome muito comum** (ex.: "café", "nível") casa com frequência. Seu peso já é dividido entre as features que aponta, mas ainda aparece em "Termos".
- **Só os nomes resolvem.** O CodeGraph liga nome a `arquivo:linha`; a resolução não segue chamadas. A navegação no código continua sendo `codegraph explore`.
- **O hook não vê skill invocada por outra skill**, só o texto que o usuário enviou.
