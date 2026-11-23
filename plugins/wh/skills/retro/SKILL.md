---
name: retro
description: Retrospective of a session: candidates to improve the agent's environment, by severity, nothing applied. Use for "retro" or, from the /wh:implementation agents, with "file: <path>".
---

# Retro

You suggest improvements to the agent's **environment** (docs, checks, skills, tools) for the next runs. Nothing is applied: the output is a list of candidates.

Argument: none, or `file: <path>` (from the `/wh:implementation` agents: a copy also goes there, ≤ 40 lines, ≤ 6 candidates). It may name a session; otherwise the current one, from memory, without rereading large logs.

The retro is written in **English**, whatever the language of the session, and is **always saved** in the clone's `retro/` folder (gitignored, local to the clone), one new file per retro, named by the current timestamp.

## Steps

1. Look for candidates in these categories, each with its evidence (what happened, command or file):
   - **Navigation:** it took long to find a file or a dependency hidden across files. Proposal: a navigation pointer (`CLAUDE.md`/`AGENTS.md`, profile `_common § Navigation`, index).
   - **Automatic check:** an error lint, typecheck, a test or a file linter would catch. First read the check the repo already has (`package.json`, build, CI): an existing check turned off or broken is the finding, not a reinvention. A repo with no guardrail (neither pre-commit nor CI running lint/typecheck/tests) is a finding by itself.
   - **Code standard:** a rule the code QA should enforce, or an existing rule to remove or clarify. A **mechanical** violation (syntactic pattern, banned API, import form, file location) becomes a deterministic check (rule in the repo's linter, pre-commit, CI job), never text. Rule text only for judgment (consistency across files, "looks like its neighbor").
   - **Steering doc:** an instruction in `CLAUDE.md`/`AGENTS.md` (repo or global) that should be a check or a QA rule; a file that is too large.
   - **Tool economy:** an expensive call that could be shorter; a CLI or MCP that burns too many tokens.
   - **No-op:** a steering instruction that does not change behavior.
   - **Information access:** crucial information the agent did not have (server log, reading an external service).
2. Severity by the cost of the problem in the session. Each candidate: category, evidence, proposal (file and change) and who applies it (repo / owner, outside the repo).
3. Save: `${CLAUDE_PLUGIN_ROOT}/skills/retro/scripts/retro_path.sh [<label>]` prints the path of the new file, `<clone root>/retro/<YYYY-MM-DD-HHMMSS>[-<label>].md` (the timestamp is the script's clock, never typed by you; it creates the folder and resolves an agent worktree to its clone). Label: none, or with `file: …/.impl/<slug>/retros/<name>.md`, `<slug>-<name>`. Write the retro to that path in the format of `${CLAUDE_PLUGIN_ROOT}/skills/implementation/REPORT.md` § Retro (title and one table, severity order). As a subagent (in an agent worktree, or in the clone): `Write` of the retro is refused, write through Bash with `cat > <path> <<'EOF'`.
4. With `file: <path>`: `cp <saved path> <path>`. Without it: present the candidates to the user in severity order, ending with the saved path.

**Done when the file exists under `retro/` at the path the script printed (and, with `file:`, its copy at `<path>`).**

## Reference

- The implementation agent has the highest context pressure (explores, writes, debugs); the QA receives a diff and has the lowest. A standards rule is enforced in the QA, not loaded into the implementer.
- `CLAUDE.md`/`AGENTS.md` enter every agent's context: navigation pointers only. Rules live in docs pointed at (profile `_common § Docs`); look for an existing doc before creating another.
- A skill fits a doc whose description must be in context, or a user command.
