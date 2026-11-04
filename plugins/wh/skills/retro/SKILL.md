---
name: retro
description: Retrospectiva de uma sessão: candidatos a melhorar o ambiente do agente, por severidade, sem aplicar nada. Use para "retro" ou, pelos agentes do /wh:implementation, com "arquivo: <caminho>".
---

# Retro

Você sugere melhorias no **ambiente** do agente (docs, checks, skills, ferramentas) para as próximas execuções. Nada é aplicado: a saída é uma lista de candidatos.

Argumento: nada (apresente ao usuário no chat) ou `arquivo: <caminho>` (grave lá, no formato de `${CLAUDE_PLUGIN_ROOT}/skills/implementation/RELATORIO.md` § Retro: ≤ 40 linhas, ≤ 6 candidatos, uma tabela). Pode citar uma sessão; sem isso, a atual, de memória, sem reler logs grandes.

## Passos

1. Procure candidatos nestas categorias, cada um com a evidência (o que aconteceu, comando ou arquivo):
   - **Navegação:** demorou para achar um arquivo ou uma dependência escondida entre arquivos. Proposta: um ponteiro de navegação (`CLAUDE.md`/`AGENTS.md`, perfil `_comum § Navegação`, índice).
   - **Checagem automática:** erro que lint, typecheck, teste ou linter de arquivos pegaria. Leia antes o check que o repo já tem (`package.json`, build, CI): check existente desligado ou quebrado é o achado, não uma reinvenção. Repo sem guardrail (nem pre-commit nem CI rodando lint/typecheck/teste) é achado por si.
   - **Padrão de código:** regra que o QA de código deveria cobrar, ou regra existente a tirar ou esclarecer. Violação **mecânica** (padrão sintático, API banida, forma de import, lugar do arquivo) vira check determinístico (regra no linter do repo, pre-commit, job de CI), nunca texto. Texto de regra só para juízo (consistência entre arquivos, "parece com o vizinho").
   - **Steering doc:** instrução do `CLAUDE.md`/`AGENTS.md` (repo ou global) que devia ser check ou regra de QA; arquivo grande demais.
   - **Economia de ferramenta:** chamada cara que dava para encurtar; CLI ou MCP que gasta token demais.
   - **No-op:** instrução de steering que não muda o comportamento.
   - **Acesso a informação:** informação crucial que o agente não tinha (log do servidor, leitura de serviço externo).
2. Severidade por custo do problema na sessão. Cada candidato: categoria, evidência, proposta (arquivo e mudança) e quem aplica (repo / dono, fora do repo).
3. Apresente ao usuário em ordem de severidade, ou grave no arquivo do argumento.

## Referência

- O agente de implementação tem a maior pressão de contexto (explora, escreve, depura); o QA recebe um diff e tem a menor. Regra de padrão é cobrada no QA, não carregada no implementador.
- `CLAUDE.md`/`AGENTS.md` entram no contexto de todo agente: só ponteiros de navegação. Regras moram em docs apontados (perfil `_comum § Docs`); procure um doc existente antes de criar outro.
- Skill serve para doc cuja descrição precisa estar no contexto, ou para comando do usuário.
