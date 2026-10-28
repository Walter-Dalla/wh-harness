# Perfil do `/wh:feature-docs`: `.claude/perfil/feature-docs.md`

Gerado pela skill `perfil`. Uma linha por fato, fonte entre colchetes, `—` na seção sem resposta.

```markdown
# Perfil do /wh:feature-docs

## Pasta
Índice e arquivos (`docs/features/README.md` + `docs/features/<feature>.md`), limite de linhas (arquivo ~50, índice ~80), idioma.

## Formato
Nome de arquivo (kebab-case, sem acento), propriedades YAML no topo (`tags`, `aliases` com nomes e ids), links (relativos `[texto](arquivo.md)` só entre notas da pasta; o resto entre crases), diagramas (` ```mermaid `), sintaxe proibida (wikilinks, callouts, embeds) e por quê (Obsidian + GitHub).

## Modelo
O esqueleto do arquivo de feature, inteiro, com as seções e a ordem (ex.: título com ids, resumo, Como funciona, Invariantes, Símbolos de entrada, Interações, Armadilhas, Pendente) e a regra de cada seção opcional.

## Fontes de regra
Docs transversais que o mapa aponta em vez de copiar (`conventions.md`, `<cliente>/CLAUDE.md`), doc de status/roadmap, changelog.

## Camadas
Como colher fatos em cada camada: backend (`codegraph explore` ou grep), cliente (índice de scripts antes de grep), contrato compartilhado, catálogos/dados. Nomes a citar por camada (classe/serviço; `class_name`/componente), sem caminho nem linha.

## Índice
As partes do índice e quando cada uma muda: tabela (arquivo, feature + ids, palavras-chave), "quem chama quem", diagrama do loop, tabela de moedas/recursos.

## Verificação
Comandos, um por linha: check de símbolos (`deploy/check-docs.sh`, exceções em `check-docs-allow.txt`), links quebrados, propriedades, sintaxe proibida, `wc -l`.
```
