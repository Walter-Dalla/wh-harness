# wh

A generic implementation harness for Claude Code. The plugin holds the procedures (skills, subagents, one hook); each project holds only its facts (commands, ports, docs, limits, glossary) in `.claude/perfil/`. A skill never names a project command: it cites a section of the project's profile.

## Install

```
claude plugin marketplace add Walter-Dalla/wh-harness
claude plugin install wh@wh-harness
```

Then run `/wh:adotar` at the root of a repository: it diagnoses what is missing and writes the profiles.

## Skills

| Command | What it does |
|---|---|
| `/wh:adotar` | onboards a repository: map, profiles, glossary, feature map, `contexto.json`, `settings.json` |
| `/wh:perfil` | writes or completes `.claude/perfil/_comum.md` and one profile per skill |
| `/wh:implementation` | a task from request to pull request: analysis and plan by an enricher subagent, parallel lanes in worktrees, code QA, final QA, retros, report |
| `/wh:limpeza` | post-run cleanup of executed plans, open items, stale docs and worktrees |
| `/wh:retro` | retrospective of a session: candidates to improve the agent's environment |
| `/wh:start-app`, `/wh:qa-visual`, `/wh:feature-docs`, `/wh:deploy`, `/wh:brainstorm` | the rest of the lifecycle, each driven by its own profile |

Subagents: `wh:impl-enrich`, `wh:impl-dev`, `wh:impl-qa`, spawned by `/wh:implementation`.

## Hook

`prompt-graph` (`UserPromptSubmit`): matches the prompt against the project's glossary, feature map and CodeGraph index and adds pointers to the context. Deterministic, no LLM, no network. It runs only in a project that has `.claude/perfil/contexto.json`, and `WH_PROMPT_GRAPH=0` turns it off for a session. Requires `python3`.

## Requirements

`git`, `bash` and `python3`. Optional, used when installed: `gh` (pull requests), `rtk` (condensed shell output), `codegraph` (code navigation).

Skills and profile templates are written in Portuguese. Full manual and source: https://github.com/Walter-Dalla/wh-harness
