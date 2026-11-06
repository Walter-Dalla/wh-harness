# Pendências de publicação · 2026-11-06

Resultado de `claude plugin validate --strict` (Claude Code 2.1.319) sobre o plugin `wh`, antes de enviar ao diretório da Anthropic (`claude.ai/directory/manage`). Primeira passada na 0.4.0; consertos aplicados na 0.6.0, no mesmo dia.

## Plugin: `claude plugin validate ./plugins/wh --strict`

Resultado: `✔ Validation passed` (exit 0).

| # | Item | Estado | Conserto |
|---|---|---|---|
| P1 | Ícone ausente (`ICON_MISSING`) | candidato criado, **dono confirma antes do primeiro envio** | `plugins/wh/.claude-plugin/icon.png`: PNG 1024×1024, 12 KB, três faixas paralelas sobre uma barra de união. Regras: PNG ou JPEG quadrado, 512 a 2048 px de lado, menos de 2 MB; SVG e WebP não são aceitos. |
| P2 | `plugins/wh/` não tinha `README.md` próprio | feito | `plugins/wh/README.md` (inglês: instalação, skills, hook, requisitos). O da raiz continua sendo o do repositório. |

Atenção ao P1: o arquivo só vira o ícone da listagem uma vez, na primeira vez que o plugin é salvo ou enviado no portal. Trocar depois não muda o ícone. O `icon.png` atual foi gerado por script, sem revisão de design: olhe-o e troque-o, se quiser outro, antes do primeiro envio.

## Marketplace: `claude plugin validate . --strict`

| # | Item | Estado | Conserto |
|---|---|---|---|
| M1 | `.claude-plugin/marketplace.json` sem `description` | feito | Campo `description` no topo do arquivo. |

## Fora do alcance do comando

O validador avisa que roda só um subconjunto das checagens do diretório. Ficam sem conferir:

- Varredura de segurança e revisão de política, feitas pelo diretório no envio.
- Regras adicionais do portal: validação local limpa não garante validação limpa lá.
- Quais componentes do `wh` (hook `UserPromptSubmit`, agentes, injeção `!cat` nas skills) carregam em claude.ai e no Cowork: ver a tabela de suporte por app em `claude.com/docs/plugins/platform-support`.

O CI (`.github/workflows/ci.yml`) passou a rodar os dois `claude plugin validate --strict` (instala o CLI por `npm`; o comando não pede login). O passo ainda não rodou no GitHub: confira o primeiro run depois do push.
