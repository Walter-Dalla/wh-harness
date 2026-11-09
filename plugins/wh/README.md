# wh

A generic implementation harness for Claude Code. The plugin holds the procedures (skills, subagents, one hook); each project holds only its facts (commands, ports, docs, limits, glossary) in `.claude/profile/`. A skill never names a project command: it cites a section of the project's profile.

## Install

```
claude plugin marketplace add Walter-Dalla/wh-harness
claude plugin install wh@wh-harness
```

Then run `/wh:adopt` at the root of a repository: it diagnoses what is missing and writes the profiles.

## Skills

| Command | What it does |
|---|---|
| `/wh:adopt` | onboards a repository: map, profiles, glossary, feature map, `context.json`, `settings.json`, project `Explore` and `Plan` agents |
| `/wh:profile` | writes or completes `.claude/profile/_common.md` and one profile per skill |
| `/wh:implementation` | a task from request to pull request: analysis and plan by an enricher subagent, parallel lanes in worktrees, code QA, final QA, retros, report |
| `/wh:cleanup` | post-run cleanup of executed plans, open items, stale docs and worktrees |
| `/wh:retro` | retrospective of a session: candidates to improve the agent's environment |
| `/wh:start-app`, `/wh:qa-visual`, `/wh:feature-docs`, `/wh:deploy`, `/wh:brainstorm` | the rest of the lifecycle, each driven by its own profile |

Subagents: `wh:impl-enrich`, `wh:impl-dev`, `wh:impl-qa`, spawned by `/wh:implementation`. `/wh:adopt agents` also copies project versions of Claude Code's `Explore` and `Plan` agents into `.claude/agents/`, so they follow the repo's navigation rules (CodeGraph, glossary, feature map, certainty marks).

## Hook

`prompt-graph` (`UserPromptSubmit`): matches the prompt against the project's glossary, feature map and CodeGraph index and adds pointers to the context. Deterministic, no LLM, no network. It runs only in a project that has `.claude/profile/context.json`, and `WH_PROMPT_GRAPH=0` turns it off for a session. Requires `python3`.

## Requirements

`git`, `bash` and `python3`. Optional, used when installed: `gh` (pull requests), `rtk` (condensed shell output), `codegraph` (code navigation).

Skills, templates, agents and docs are written in English (since 0.7.0). Full manual and source: https://github.com/Walter-Dalla/wh-harness
