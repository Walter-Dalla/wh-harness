---
name: profile
description: Generates or completes a skill's project profile (.claude/profile/_common.md and <skill>.md) from its PROFILE.md. Called by another skill or with /wh:profile <skill>.
---

# Project profile

Argument: the skill name (`start-app`, `deploy`, `implementation`…), and `defer` after it when the calling skill will confirm the `[inferred]` lines itself (§ 3). No argument, or only `defer`: `implementation` plus the skills whose source exists in the repo (`deploy` with a deploy folder or workflow; `start-app` with a service or client to bring up; `qa-visual` with a QA harness; `feature-docs` with a features folder; `cleanup` with a changelog or plan folder); `brainstorm` only with an argument. Templates in `${CLAUDE_PLUGIN_ROOT}/skills/*/PROFILE.md`. A profile for a skill the repo does not use is versioned junk, not one more `—`.

A **profile** is what a generic skill needs to know about the repository and cannot discover on its own: commands, paths, ports, docs, limits. Facts only, each with its source in brackets; the procedure stays in the skill. Two files, versioned in the repo, read only by the skill (they never load on their own):

| File | Template | Content |
|---|---|---|
| `.claude/profile/_common.md` | [`COMMON.md`](COMMON.md) | what every skill uses: clone, toolchain, git, ports, navigation, docs, limits |
| `.claude/profile/<skill>.md` | `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/PROFILE.md` | only what that skill uses; cites `_common § X` instead of repeating |

## 1. Difference

`python3 -I "${CLAUDE_PLUGIN_ROOT}/skills/adopt/scripts/check.py" --root .` already computes it: the line `profile <skill>` says `MISSING <path>` (no file), `MISSING … missing sections: <list>` or `OK`, and the `WARN` lines say what is too long, `[inferred]` or `—`. Read that output instead of comparing the template and the file by hand; open the template only for the sections you will write. An extra section in the file stays (repo knowledge). Complete file = say so and stop.

**Done when every template section is classified: present or missing.**

## 2. Sources

For each missing section, in this order, stopping at the first that answers: `CLAUDE.md`/`AGENTS.md` and the docs they point at; `.claude/profile/*.md` already written; a profile of before 0.7.0 in `.claude/perfil/` (`_comum.md`, `<skill>.md`, Portuguese headings: its facts move to the section of the same meaning); the project's old skill in `.claude/skills/<skill>/SKILL.md` (migration: its facts move into the profile); CI workflows (`.github/workflows/*`); build and dev scripts (`package.json`, `Makefile`, `*.sln`, `pyproject.toml`, `scripts/`, `deploy/`); `README`. Each profile line ends with its source: `[CLAUDE.md]`, `[ci: tests.yml]`, `[scripts/dev.sh]`, `[old skill]`, `[inferred]`. Repo without an answer: the section stays `—` (the skill skips the phase that depends on it and says so).

**Done when every missing section has text with a source or `—`.**

## 3. Confirm

`[inferred]` lines go to the owner through `AskUserQuestion`: up to 4 questions per call (2–4 options each), one question per profile section with its lines as options (plus "other"); more than 4 sections, calls in sequence. With `defer`, or in a session without an owner (subagent): they stay marked `[inferred]` and the final answer lists them; the caller asks.

## 4. Write

Facts, one line per fact, commands in backticks and complete (with `<port>`, `<slug>`, `<filter>` where the skill substitutes). The implementation profile's § Commands is written as `` <key>: `<command>` `` lines, the five keys, `—` where the repo has none, and its prose sections cite the key instead of repeating the command. Nothing `_common.md` already says: cite `_common § Git`. No procedure ("first do X, then Y"): that belongs to the skill. Target: `_common.md` ≤ 40 lines, `<skill>.md` ≤ 60; past that, the excess becomes a repo doc the profile points at.

`prompt-graph` hook: `.claude/profile/context.json` missing and the repo has a glossary or a feature map (`_common § Docs`) = write it with only the keys that differ from the default (`glossario`, `features`, `indice_features`, `codegraph`, `idioma`; defaults in `DEFAULTS` of `${CLAUDE_PLUGIN_ROOT}/scripts/prompt_graph.py`). Neither source: do not create the file.

Migration of the project's old skill: once the profile holds its facts, `git rm -r .claude/skills/<skill>` (the same name in the project shadows the user's skill). Scripts and harness the old skill carried go to a repo folder (`deploy/`, `tools/`, `scripts/`) and the profile points there. Migration of a profile of before 0.7.0: once the new profile holds its facts, `git rm -r .claude/perfil` (or first `git mv .claude/perfil/contexto.json .claude/profile/context.json` when the hook was on).

**Done when `.claude/profile/_common.md` and `.claude/profile/<skill>.md` have every template section, every line with a source, and the project's old skill (if there was one) is gone.**

## 5. Answer

Sections written, `—` sections, unconfirmed `[inferred]` lines, and the hook: `context.json` written, already present, or "prompt-graph hook off: no sources (`/wh:adopt sources` seeds glossary and feature map)". The calling skill reads the written files with `Read` (its `!cat` injection ran earlier). Commit only if the owner asks or the calling skill says so (`/wh:implementation` commits the profile on the task branch).
