---
name: adopt
description: Turns the wh harness on in a repository that does not have it yet: diagnoses what is missing, creates CLAUDE.md, profiles, glossary, feature map, context.json, settings.json and the project's Explore and Plan agents, and validates. Use for "adopt the harness", "prepare the project for wh", or /wh:adopt.
---

# Adopt the harness

You are at the root of a repository that wants to use the `wh` plugin. The plugin already has the procedures; this repo does not yet have the **facts** (`.claude/profile/`), the hook's **sources** (glossary, feature map) or the plugin **declaration**. This skill creates what is missing and validates. Nothing of the project enters the plugin: everything you write stays in the repo.

Argument: none (everything) or a list of what to do: `check` (diagnosis only), `profiles`, `sources` (glossary + feature map), `hook` (`context.json`), `plugin` (`settings.json` + `.gitignore`), `agents` (the project's `Explore` and `Plan` agents). E.g. `/wh:adopt check`, `/wh:adopt profiles hook`, `/wh:adopt agents`.

Diagnosis (injected; runs before you read this):
!`python3 -I "${CLAUDE_PLUGIN_ROOT}/skills/adopt/scripts/check.py" --root . 2>&1 || true`

## 1. Diagnose

Read the diagnosis above. `MISSING` = this skill creates it; `OUTDATED` = this skill recopies it (agent templates, § 5); `WARN` = the owner's or another skill's decision (said in the detail); `OK` = do not touch. With `check`: present the diagnosis with one line of what each `MISSING` or `OUTDATED` would require and stop.

Confirm the root: `git rev-parse --show-toplevel` equals the cwd. Monorepo: adoption is per git root, not per package; `context.json` is looked up walking up the tree from the session's cwd.

**Done when every line of the diagnosis is classified: create here, ask the owner, or leave.**

## 2. Repo map (`CLAUDE.md`)

`MISSING repo map`: write `CLAUDE.md` at the root, ≤ 30 lines, navigation pointers only: what the project is (one line), where each layer lives (folders), how to build and test (the commands the `README`, CI and build scripts show), which docs to read and when. Sources: `README`, `.github/workflows/*`, `package.json`/`pyproject.toml`/`*.sln`/`Makefile`, repo tree (`ls`, 2 levels). No style rule here: rules live in a doc pointed at. `AGENTS.md` already exists = do not create `CLAUDE.md`; the `profile` skill reads both.

**Done when the map exists and every path cited in it exists.**

## 3. Profiles

`Skill(wh:profile)` with no argument: writes `_common.md`, `implementation.md` and the profiles of the skills whose source exists in the repo. Owner present: the `profile` skill confirms the `[inferred]` lines; session without an owner (`-p`, subagent): `Skill(wh:profile, "defer")` and list the lines in the final report. Then `Read` the written files.

`WARN old skill` (folder `.claude/skills/<skill>` with the same name as a plugin skill): the `profile` skill moves its facts into the profile and removes the folder (its § 4). Check that it did.

**Done when `.claude/profile/_common.md` and `implementation.md` exist with every template section and the diagnosis (§ 6) reports no `MISSING profile`.**

## 4. Hook sources

Only when the repo has a domain for it (entities, services, screens with business names). A small library or a script with no vocabulary of its own: skip and say you skipped.

- **Glossary** (`MISSING glossario`): create `docs/GLOSSARY.md`: `##` sections per area, each with the table `| Business | Code | Avoid / note |` (Code in backticks; Avoid in double quotes), and `## Pitfalls` with `| In the code | Means | Why |`. Seed it with the terms the code shows unambiguously: entity, service, route, enum names (`codegraph explore` if `.codegraph/` exists; otherwise the tree and the model files). Business column: the name the `README`/docs use; no business name, the identifier itself. Avoid column: only synonyms the repo actually confuses (docs, issues, commits); nothing invented. 10 to 30 lines; the owner completes it.
- **Feature map** (`MISSING features`/`indice_features`): create `docs/features/README.md` with the table `| File | Feature | Look here when the task talks about… |` (link in the first cell; the others become comma-separated keywords) and one file per candidate feature: a module or folder with its own user loop and its own owner in the code (service/entity/endpoints or panel). Each file: `aliases` frontmatter, `# Title`, one summary line, `## Entry symbols` (identifiers in backticks, read from the code), `## Interactions` (`[x](x.md)` links only for dependencies the code shows). ≤ 20 lines each: `/wh:feature-docs` fattens them later, once there is a profile. More than 8 candidates: create the 8 most central and list the rest in the index without a file (one line with `—` in the File column).
- Language: the one of the repo's docs. The hook accepts the section names in English (`Entry symbols`, `Interactions`, `Pitfalls`) and in Portuguese; in English set `"idioma": "en"` in `context.json`.

**Done when the glossary and the index parse: `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/prompt_graph.py" --build --root .` shows terms and features > 0 (needs the `context.json` of § 5).**

## 5. `context.json`, `settings.json`, `.gitignore`, agents

- `MISSING context.json`: write `.claude/profile/context.json` with only the keys whose value differs from the default (`glossario`, `features`, `indice_features`, `codegraph`, `idioma`; defaults and the other keys in `DEFAULTS` of `${CLAUDE_PLUGIN_ROOT}/scripts/prompt_graph.py`). No glossary nor features (skipped § 4): do not create the file and say "hook off: no sources".
- `MISSING settings.json`: create or complete `.claude/settings.json` (merge: never delete existing keys) with `extraKnownMarketplaces.wh-harness` (`source: github`, `repo: Walter-Dalla/wh-harness`) and `enabledPlugins."wh@wh-harness": true`. Pin a version (`"ref": "<tag>"`) only if the owner asked.
- `.gitignore`: add `.codegraph/` if it is not there. `.impl/` goes in `.git/info/exclude` (`/wh:implementation` does it); do not put it in `.gitignore`.
- **Pending folder** (`WARN links` citing the folder of `_common § Pending`, or the folder absent): create it with a `README.md`: one paragraph pointing at the format `${CLAUDE_PLUGIN_ROOT}/skills/implementation/PENDING.md`, followed by a copy of its `## Format` block; it is the home of the owner's open items and the intake of `/wh:implementation`.
- `WARN codegraph` with the CLI present and the index missing: **do not run** `codegraph init`; indexing is the owner's decision. It enters the report as an open item with the command.
- **Agents** (`MISSING agents` or `OUTDATED agents`): copy `${CLAUDE_PLUGIN_ROOT}/skills/adopt/templates/agents/Explore.md` and `Plan.md` to `.claude/agents/`, byte for byte (`cp`). A project agent with the same name wins over Claude Code's native `Explore` and `Plan` (seen in 2.1.319), so the main session's exploration and planning subagents follow the repo's rules: CodeGraph, glossary and feature map read from `.claude/profile/`, certainty marks, impact radius. The template has no project fact; the copy reads `_common § Navigation` and `_common § Docs` at run time. The `<!-- wh-template: <name> <n> -->` marker in the body is what the diagnosis compares: it rises only when the template changes. `WARN agents` (the file exists without a marker) is the owner's: do not overwrite; say so in the report. A plugin agent (`plugins/wh/agents/`) gets the `wh:` namespace and does not replace a native one; that is why the copy lives in the project.

**Done when the three files exist, `python3 -m json.tool` accepts both JSON files, and the diagnosis reports `OK agents` for both templates (or `WARN agents`, the owner's).**

## 6. Validate

1. Run `python3 -I "${CLAUDE_PLUGIN_ROOT}/skills/adopt/scripts/check.py" --root .` again: zero `MISSING` and zero `OUTDATED` (apart from the ones the owner decided to leave, said in the report).
2. Hook: `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/prompt_graph.py" --query "<sentence with 2 glossary terms>" --root . --explain`: the right feature appears under "Read". It does not: add the word to the index line or to the `aliases`.
3. Every path cited in `CLAUDE.md`, in the profiles (`_common § Docs`) and in `context.json` exists: the `links` line of the diagnosis of step 1 is `OK` (a `WARN links` lists each absent path: fix the citation or create the file).

**Done when the three pass.**

## 7. Report

In order: files created and changed (one per line, the pending folder's `README.md` among them); what stayed `WARN` and who resolves it (owner: `codegraph init -y .`, `[inferred]` lines, optional profiles; another skill: `/wh:feature-docs` to fatten the map); what was skipped and why; and the two final steps only the owner does: commit `.claude/profile/`, `.claude/agents/`, `.claude/settings.json`, `CLAUDE.md`, `docs/` and open a new session (hooks, plugins and agents load at session start: the copied `Explore` and `Plan` only take effect in the next one). Commit only if the owner asks.
