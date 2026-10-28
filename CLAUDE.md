# wh-harness

Plugin `wh` para Claude Code: procedimentos genéricos (skills, agentes, hook) que leem os fatos de cada projeto em `.claude/perfil/`.

- Mapa completo e mecanismos: `docs/MANUAL.pt-BR.md`. Visão curta em inglês: `README.md`.
- Skills: `plugins/wh/skills/<skill>/SKILL.md` (+ `PERFIL.md`, o modelo do perfil). Agentes: `plugins/wh/agents/`. Hook: `plugins/wh/hooks/hooks.json` → `plugins/wh/scripts/prompt_graph.py`.
- Regra: a skill tem o procedimento, o perfil tem os fatos. Nenhuma skill ou agente cita um comando de projeto; cita `perfil § Seção`.
- Testes: `python3 -m unittest discover -s tests` (hook contra `examples/demo`, `escopo.sh`, `preflight.sh`). Scripts de shell passam por `bash -n` e `shellcheck -S warning` no CI.
- Mudou uma skill ou o hook: suba `version` em `plugins/wh/.claude-plugin/plugin.json` e ajuste o `MANUAL`.
