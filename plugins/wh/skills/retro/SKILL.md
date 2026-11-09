---
name: retro
description: Retrospective of a session: candidates to improve the agent's environment, by severity, nothing applied. Use for "retro" or, from the /wh:implementation agents, with "file: <path>".
---

# Retro

You suggest improvements to the agent's **environment** (docs, checks, skills, tools) for the next runs. Nothing is applied: the output is a list of candidates.

Argument: none (present to the user in the chat) or `file: <path>` (write it there, in the format of `${CLAUDE_PLUGIN_ROOT}/skills/implementation/REPORT.md` § Retro: ≤ 40 lines, ≤ 6 candidates, one table; path outside your agent worktree: `Write` is refused, write through Bash with `cat > <path> <<'EOF'`). It may name a session; otherwise the current one, from memory, without rereading large logs.

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
3. Present to the user in severity order, or write to the file from the argument.

## Reference

- The implementation agent has the highest context pressure (explores, writes, debugs); the QA receives a diff and has the lowest. A standards rule is enforced in the QA, not loaded into the implementer.
- `CLAUDE.md`/`AGENTS.md` enter every agent's context: navigation pointers only. Rules live in docs pointed at (profile `_common § Docs`); look for an existing doc before creating another.
- A skill fits a doc whose description must be in context, or a user command.
