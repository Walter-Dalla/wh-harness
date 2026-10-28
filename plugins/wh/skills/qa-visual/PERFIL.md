# Perfil do `/wh:qa-visual`: `.claude/perfil/qa-visual.md`

Gerado pela skill `perfil`. Uma linha por fato, fonte entre colchetes, `—` na seção sem resposta. O harness (driver, ops, scripts) é código do repo: o perfil aponta a pasta e o doc dele, não os descreve.

```markdown
# Perfil do /wh:qa-visual

## Harness
Pasta no repo (ex.: `deploy/qa/`) e o doc das ops e scripts (`deploy/qa/HARNESS.md`). Scripts, um por linha: setup, subir o serviço do QA (porta, banco isolado, token de admin), rodar cenário (`run.sh <feature> <cenário> <WxH> [id|new] [args]`), teardown. Cenário de fumaça. Onde os cenários da rodada ficam depois do teardown.

## Ambiente
Engine/versão e binário por checkout, cena/entrada do cliente, lista canônica de args de debug (arquivo), o que só roda em um SO.

## Entrada
Padrões de `--res` (incluindo o retrato) e `--lang`; como o idioma troca.

## Saída
Layout de `qa/`: relatório, prints (`qa/screenshots/<feature>/<cenário>-<WxH>/NN-passo.png`, preview, `.ui.json`), logs, dados do serviço, backup do estado local, cenários.

## Contexto
Docs que dão o critério de "correto" (regras de camada, mapa de features, status, pendências conhecidas), números (`Balance`, catálogos).

## Checklist
Doc com o que verificar por feature, como ler os prints e o que não é bug (`deploy/qa/CHECKLIST.md`).

## Fixtures
Como montar estado de partida (script de fixture, `PUT`s, ferramenta de nível/saldo pelo admin local), estado do usuário novo, o que exige recurso sem caminho pela UI.

## Tempos
Ação mais curta e seu tempo, folga das esperas, limite a partir do qual um item vira "Parcial", animações que atrasam leitura (saldo anima ~2 s).

## Armadilhas
Uma por linha: textos que mudam com o estado, elementos duplicados (tooltip + painel), abas que exigem scroll no retrato, detecção de painel.

## Pendências
Doc onde um achado que sobrevive à rodada entra (linha em `FEATURES.md › Dívida técnica`), e onde um plano de correção temporário mora.
```
