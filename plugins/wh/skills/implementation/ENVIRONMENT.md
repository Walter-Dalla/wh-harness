# Environment and protocol of `/wh:implementation`

Everything runs in the `_common` § Clone checkout (the orchestrator's session opens there) and in the agent worktrees born from it. The clone's native toolchain. The limits of `_common` § Limits hold for every agent (the owner's ports, production, real MCPs).

## Ports

Only if profile § Disposable service exists. From the port range of `_common` § Ports, in order:

| Port | Who |
|---|---|
| 1st | orchestrator: small-task item that needs the service; enricher: Acceptance at the tip (the two never use the service at the same time) |
| 2nd–4th | `impl-dev` lanes, one per lane (up to 3 in parallel) |
| 5th | FIX lane or reserve |
| 6th | `impl-qa` mode `final` (the profile's visual/e2e QA may bring up its own service; it picks a free port, never killing what already sits on one) |

## Scripts (`${CLAUDE_PLUGIN_ROOT}/skills/implementation/scripts/`)

| Script | Who runs it | Does |
|---|---|---|
| `preflight.sh --base <hash> [--branch <b>] [--port <p>] [--lane <lane.md>] [--protected <a,b>]` | `impl-dev` and `impl-qa`, before any `git reset`/`branch` | checks agent worktree, branch, clean worktree, existing base, free port, lane and board; `PREFLIGHT FAILED` = `BLOCKED`, touching nothing |
| `scope.sh <lane.md> <base> [<ref>]` | `impl-dev` at the end, orchestrator before the merge | changed files × `Owns:`/`May touch`/`Union:` of the lane (paths in backticks); `OUTSIDE:` = the lane fixes it before the merge |

## Tools (each only if installed; present, mandatory from the first step)

### RTK (Bash output)

With `rtk` installed, every Bash output arrives condensed: RTK keeps the signal (errors, counts, paths, exit code) and drops the noise.

- Treat the output as the complete result; do not repeat the command "to see it whole".
- Batch related commands into one call (`cmd1 && cmd2`, or `;`) instead of one call per command: each turn costs more than the output. Exception, the agent worktree with the isolation guard: there § Bash in the agent worktree and profile § Worktree commands apply (git by the absolute path the prompt's `Commands:` line gives, `<git> -C <worktree> …`, one command per call; RTK rewrites a bare `git` and the guard refuses it).
- Truncated output says in its own text how to recover the rest; follow that path.
- `rtk proxy <cmd>` only when the output is unusable: empty when something was expected, contradicting the exit code, or truncated with no recovery path.
- Even with RTK, filter what is large at the source (`2>&1 | tail -30`, `grep -E`): the commands of profile § Tests and § Checks already come filtered. The verdict is always the command's exit, never the filter's (§ Tests and checks).

Without `rtk` on the PATH: raw output; the profile's filters remain mandatory.

### CodeGraph (`codegraph` on the PATH)

Repo with `.codegraph/`: in the worktree, `codegraph init -y .` once before editing (to verify: in a large repo, copying the clone's `.codegraph/` and running `codegraph sync .` may be cheaper than reindexing per lane); in the clone, `codegraph sync .`. `codegraph explore -p . "<symbols or question>"` before claiming anything about indexed code, output treated as read; `codegraph sync .` after editing. `grep`/`Read` for what the index does not cover (`_common § Navigation`) and for every repo without an index.

## States

Every agent answer and every `END` line of the board ends in one of these states, with the evidence beside it:

| State | When | Next action |
|---|---|---|
| `DONE` | every item with a commit and Acceptance run and green | move on |
| `PARTIAL` | part of the items done (context, time, skipped item) | resume from the checkpoint |
| `WAITING` | stopped on a `QUESTION` with no independent item | the answer resumes the agent |
| `HUMAN_DECISION` | a part only the owner does or decides (`HUMAN` line on the board) | record and go on with the rest |
| `BLOCKED` | environment or tool prevents going on (preflight, refused push, build broken outside the lane) | the orchestrator diagnoses |
| `FAILED` | final verification red (suite, check, scope) | fix before delivering |

**Evidence** of an item: `item · commit · Acceptance (command) · exit code · what the command covers`. Not evidence: a command not run, truncated or interrupted output, a test of another area, or another agent's report without checking the repository. Exit 0 of a test that does not exercise the item is not either.

## Checkpoint

In `<root>/.impl/<slug>/progress/<lane>.md` (path from the prompt; outside git through the `.impl/` exclude), never inside the worktree, which disappears when the agent ends. Rewritten after each item, so a new agent continues without the previous one's memory:

```markdown
Lane: <lane> · base <hash> · tip <hash>
Done: <id> <commit> <Acceptance: exit> (one per line)
Current: <id> · uncommitted: <files or "nothing">
Tests: <command> → <result>
Next action: <exact>
Open: <pending QUESTION/HUMAN>
Fixes requested: <QA-… ids received and not committed, with the QA file, or "none">
```

## Files outside the worktree

Retro, checkpoint, QA output and Acceptance log go to the absolute paths from the prompt, in `<root>/.impl/<slug>/` (the folders `qa/`, `retros/`, `progress/` and `acceptance/` already exist: the orchestrator creates them in phase 1). In an agent worktree the isolation guard refuses `Write`/`Edit` on those paths (seen in Claude Code 2.1.312): write through Bash, `cat > <absolute path> <<'EOF'` … `EOF`, one simple call per file, never `Write`/`Edit` outside the worktree. In the clone (enricher, QA mode `code`) `Write` works. Heredoc also refused: the content goes in your final answer, marked with the destination path, and the orchestrator writes it. The board accepts `printf … >> <board>`.

## Bash in the agent worktree

The same guard refuses the command it cannot verify ("too complex to verify"). Refused (seen in the test drives, Claude Code 2.1.312 and 2.1.319):

- a compound command that mentions `git`, and `$(…)` substitution;
- an environment variable in front of the command (`HOME=<folder> command`, `VAR=x command`) and `env …` (`env -u VAR command`);
- a heredoc or program assembled on the fly for an interpreter (`python3 - <<'EOF'`, `python3 -c "$var"`), and a test with a computed operand;
- a loop (`for`, `while`), a long script in a single call, `cd` outside the worktree.

One simple command per call; `git -C <worktree> reset --hard <hash>` in its own call; a value from another command (date, hash) = run it first and paste the literal result; a script of more than one line = a file inside the worktree, outside the commit, run by name. A command that only passes outside the worktree (Acceptance marked "clone only" in the lane): do not insist; a `WARNING` line on the board and the orchestrator runs it (`LANES.md` §3, step 1). Whatever else the guard refuses in this repo: profile § Worktree commands.

## Disposable service

The command of profile § Disposable service with your port and a disposable state (`<slug>-<port>` in the database or folder name), at the worktree root, in the background (`run_in_background`); ready when the profile's health check responds. Stop it at the end (`kill <pid>` of the process you started). Never the owner's data state.

## Tests and checks

Commands of profile § Tests and § Checks, output always filtered. The verdict is the exit code of the suite command: with a pipe (`| tail`, `| grep`) the exit is the filter's, so run the runner's quiet mode without a pipe, or put `set -o pipefail` in front. Test choice per item: localized change = the area test; contract = producer and consumer tests; shared infrastructure = tests of the dependent areas; the whole suite only at the end of the lane and in the final QA. Contract fixture: through profile § Contract, then the `git diff` of the fixture folder, field by field.

## Navigation

`_common § Navigation`; CodeGraph: § Tools above. No index: `grep`/`Read` by snippet.
