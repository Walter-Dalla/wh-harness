# wh-harness

`wh` plugin for Claude Code: generic procedures (skills, agents, hook) that read each project's facts from `.claude/profile/`.

- Full map and mechanisms: `docs/MANUAL.md`. Short overview: `README.md`.
- Skills: `plugins/wh/skills/<skill>/SKILL.md` (+ `PROFILE.md`, the profile template). Agents: `plugins/wh/agents/`. Hook: `plugins/wh/hooks/hooks.json` → `plugins/wh/scripts/prompt_graph.py`.
- Everything is written in English: skills, templates, agents, scripts, docs. A project's profile follows the `##` headings of the template.
- Rule: the skill has the procedure, the profile has the facts. No skill or agent cites a project command; it cites `profile § Section`.
- Tests: `python3 -m unittest discover -s tests` (hook against `examples/demo`, `scope.sh`, `preflight.sh`, `check.py`, section references). Shell scripts go through `bash -n` and `shellcheck -S warning` in CI.
- Changed a skill or the hook: bump `version` in `plugins/wh/.claude-plugin/plugin.json` and adjust the `MANUAL`.
