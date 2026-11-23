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
| `intake.sh <root> [--dir <folder>] [<arg>…] \| --next` | orchestrator, phase 1 (intake) and close (id of a new pending file) | reads `<root>/pending/` (`--dir`: the folder the owner named instead); prints `PENDING_DIR=`, `INTAKE=file\|raw`, `PENDING=`, `SLUG=`, `INTAKE OK`; arguments that only say "all" (`all`, `todas as pendências`) count as no argument; the folder is local to the clone (not ignored yet: it goes in `.git/info/exclude`); `--next` prints only the next `P-NNN` never used, counting the folder, its `done/` and every pending file the git history ever added; `INTAKE FAILED` = stop |
| `impl_env.sh <slug> [--main <b>] [--remote <r>] [--no-pull] \| --pull-only [--main <b>] [--remote <r>]` | orchestrator, phase 1: `--pull-only` before the intake, then once with the slug | checks root, main branch, clean status, remote, `pull --ff-only` (skipped with `--no-pull`); `--pull-only` stops there, prints `ROOT=`, `MAIN=`, `REMOTE=`, `BASE=` and `PULL OK` and creates nothing; with the slug: exclude lines, `.impl/<slug>/` folders (`qa/`, `retros/`, `progress/`, `acceptance/`, `agent_chat/`) and board, PR mode, CodeGraph sync, integration worktree; prints the task's `KEY=VALUE` facts and writes them to `<root>/.impl/<slug>/env`; `ENV FAILED` = stop. `--main` is the base branch of the run: the repo's main, or the branch the owner names as the base (stacked work; it must be the clone's checkout and exist on the remote), and every later `--main`/`<main>` is that same `MAIN`. An `impl/<slug>` that already exists: `REUSED=worktree` (the run goes on in its worktree), `branch` (a run to resume, its worktree recreated) or `fast-forwarded` (the leftover of a run that landed, nothing ahead of `<main>`: brought to it); `AHEAD`/`BEHIND` count its commits against `<main>` (`BEHIND` above zero = `<main>` moved since the base: phase 5 merges it); ahead and behind with no worktree = `ENV FAILED`, the owner says whether it landed or resumes |
| `board.sh <board> <who> <KIND> <text…>` | every agent, for every board line | appends `<date> | <who> | <KIND> | <text>` with a fresh UTC timestamp; one simple command (passes the worktree guard) |
| `agent_chat.sh <impl> ask <lane> <item> <who> <text…> \| <file> answer <who> <impact> <text…>` | orchestrator when relaying a consultation; enricher (or orchestrator) when answering | `ask` creates `<impl>/agent_chat/NN-<lane>-<item>.md` (`## Question (<who>)`), `answer` appends `## Answer (<who>) · impact: <impact>`; `NN` is taken under a lock file (`agent_chat/.lock`); both print only the file's absolute path; `AGENT_CHAT FAILED` on a missing folder or file, an existing `NN` file or a held lock |
| `lane_prompt.sh <slug> <lane> [--qa] [--remote <r>] [--main <b>] [--continuation <text>] [--retest <ids>] [--areas <text>] [--verify <ids>] [--gates yes\|no] [--retro yes\|no]` | orchestrator, at the clone root, before each `Agent(...)` of a lane or a QA | prints the agent's prompt in the format of the prompt blocks of `LANES.md` §2 and `SKILL.md` phases 4–5; `--qa` with a lane = mode `code` prompt and `<root>/.impl/<slug>/qa/<lane>.diff` written; `--qa` with `code` = the small-task code QA (`Lane: all`, diff base `<main>`); `--qa` with `final` = mode `final`; `--main` and `--remote` default to the `MAIN=` and `REMOTE=` of `<root>/.impl/<slug>/env`, so no call needs them; `Profile:` is the integration worktree's copy (the clone's goes stale once a lane changes the profile); `LANE_PROMPT FAILED` (exit 1) = stop |
| `acceptance.py <lane.md or PLAN.md> <worktree> [--only <ids>] [--log <dir> --lane <l>]` | enricher (Acceptance at the tip, `WAVE`), `impl-dev` (per item, with `--log`) | runs each item's `Acceptance:` command in the worktree, prints `<id> · exit <n>`, writes `<dir>/<lane>-<id>.log` as the command runs (a long one can be followed there); only a `## <name>-<number>` heading is an item; `<id> · WARNING · test file <path> does not exist` under a green item = the green proves nothing (the runner skipped the file): guard the command with `test -f <path> &&` |
| `profile_run.sh <key> [<worktree>=.] [--port <p>] [--slug <s>] [--log <file>] [--wait <s>] [--print]` | orchestrator at end of wave and in phase 5; `impl-qa` mode `final`; `impl-dev` (suite, typecheck, service) | runs the `<key>` (`build`, `suite`, `typecheck`, `service`, `health`) of profile § Commands in the worktree, no pipe; prints the last 30 lines and `PROFILE_RUN <key>: exit <n>`, exits `<n>`; `PROFILE_RUN <key>: skipped` (exit 0) when the key is `—`; `health` is retried once a second for up to `--wait` seconds (default 20) while it fails; `--print` prints the command with `<port>` and `<slug>` replaced; `PROFILE_RUN FAILED` (exit 2) = no § Commands or a malformed key: the prose of the profile section, by hand |
| `preflight.sh --base <hash> [--branch <b>] [--port <p>] [--lane <lane.md>] [--protected <a,b>]` | `impl-dev` and `impl-qa`, before any `git reset`/`branch` | checks agent worktree, branch, clean worktree, existing base, free port, lane and board; `PREFLIGHT FAILED` = `BLOCKED`, touching nothing |
| `scope.sh [--classify] <lane.md> <base> [<ref>]` | `impl-dev` at the end, orchestrator before the merge; `--classify`: `wave_prep.sh` | changed files × `Owns:`/`May touch`/`Union:` of the lane (paths in backticks); `OUTSIDE:` = the lane fixes it before the merge; `--classify` prints `OWN:`/`UNION:`/`MAY:`/`OUTSIDE:` per changed file, exit 0 |
| `wave_prep.sh <slug> <wave> <base> <lane>…` | orchestrator, at the clone root, before each wave after the first | runs every pending Acceptance at the tip of `<intwt>`, takes the board's `CONTRACT` lines since the last `WAVE` line and the moved files (`git diff --name-status <base>..<tip>`, classified against the pending lanes), writes `<root>/.impl/<slug>/wave-<wave>.md`, prints its path and `WAVE CLEAN` (exit 0) or `WAVE ENRICHER: <g> green item(s), <c> CONTRACT line(s), <o> owned file(s) moved` (exit 3); `WAVE_PREP FAILED` (exit 1) = stop |
| `merge_lane.sh <integration worktree> <slug> <lane> <remote> [<main>]` | orchestrator only, at each lane merge | refuses a worktree not on `impl/<slug>` (`MERGE REFUSED`, exit 1); fetches and merges `<remote>/impl/<slug>-<lane>` with `--no-ff` (`MERGED`); `MERGE CONFLICT` exit 3 leaves the merge in progress; `MAIN MOVED: <n> commit(s)` when `<remote>/<main>` advanced since the base |
| `cleanup_worktrees.sh <root> <slug> [--main <b>] [--integration] [--dry-run]` | orchestrator, phase 6; `/wh:cleanup` § 6 | removes the run's worktrees (`impl/<slug>-*`, `worktree-agent-*` on a commit of `<main>..impl/<slug>`), saving changes as `wip: <branch>`; `--integration` also removes `impl/<slug>`'s; everything else `KEPT` |
| `report_skeleton.py <slug> [--root <dir>] [--pr github\|none] [--out <file>]` | orchestrator, phase 6 (`python3 -I`) | writes the report skeleton in the headings of `REPORT.md`, filled from the board, the QA files, `agent_chat/` and the retros (retro rows merged only when Category and Proposal are equal), `TODO(orchestrator): …` where judgment is needed; `--out` prints `WROTE <path>`; `REPORT_SKELETON FAILED` (exit 2) on a bad call or a missing `.impl/<slug>/` |
| `agent_cost.py --session <id> [--cwd <dir>] [--projects <dir>]` | orchestrator, phase 6 (`python3 -I`), for the report's § Cost | reads the session's transcripts (main session and `subagents/agent-*.jsonl`, read only) and prints one table row per agent: model, requests, input, cache write, cache read and output tokens, and its share of the weighted tokens (a one-hour cache write weighs ×2); `AGENT_COST FAILED` (exit 2) = "not measured" in the report |

**Free text as an argument** (the owner's request, an agent's question or answer): never inside double quotes, where `$`, backticks and `"` of the text expand or break the command; each argument in single quotes, every `'` in it written as `'\''`. For `intake.sh`, one single-quoted argument per word the owner typed (an id `P-NNN` or a path stays its own argument, so it resolves).

`cleanup_inventory.py` (`ITEMS`, `COMMITS WITHOUT ITEM`, `OLD PATHS`, `OLD NAMES` of a run) lives in `${CLAUDE_PLUGIN_ROOT}/skills/cleanup/scripts/`: called by `/wh:cleanup` § 1 and by phase 6.

## Tools (each only if installed; present, mandatory from the first step)

### RTK (Bash output)

With `rtk` installed, every Bash output arrives condensed: RTK keeps the signal (errors, counts, paths, exit code) and drops the noise.

- Treat the output as the complete result; do not repeat the command "to see it whole".
- Batch related commands into one call (`cmd1 && cmd2`, or `;`) instead of one call per command: each turn costs more than the output. Exception, the agent worktree with the isolation guard: there § Bash in the agent worktree and profile § Worktree commands apply (git by the absolute path the prompt's `Commands:` line gives, `<git> -C <worktree> …`, one command per call; RTK rewrites a bare `git` and the guard refuses it).
- Truncated output says in its own text how to recover the rest; follow that path.
- A hook that rewrites a command after the permission review (`cat` → `rtk read`, `ls` → `rtk ls`, `grep` → `rtk grep`) makes auto mode hand the call back unreviewed ("a hook changed this call's input", seen in 5 runs of 2026-11): type the `rtk` form yourself from the first call (`rtk read <file>`, `rtk ls <dir>`, `rtk grep …`), or `Read` for a file. A call handed back that way: issue it again exactly as the message quotes it.
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
Open: <pending QUESTION/HUMAN, with the agent_chat/ file path>
Fixes requested: <QA-… ids received and not committed, with the QA file, or "none">
```

**Interrupted run** (session cut, usage limit, restart): the orchestrator takes the state from disk, never from memory: `<root>/.impl/<slug>/env` (the facts of phase 1), the last `WAVE`, `MERGE` and `END` lines of the board, `progress/*.md` and `git -C <intwt> log --oneline <main>..`; then it goes on from that step. A lane with no `END` line: `LANES.md` §3, step 9. The enricher after a restart: `CONSULT.md`.

## Files outside the worktree

Retro, checkpoint, QA output and Acceptance log go to the absolute paths from the prompt, in `<root>/.impl/<slug>/` (the folders `qa/`, `retros/`, `progress/`, `acceptance/` and `agent_chat/` already exist: the orchestrator creates them in phase 1). In an agent worktree the isolation guard refuses `Write`/`Edit` on those paths (seen in Claude Code 2.1.312): write through Bash, `cat > <absolute path> <<'EOF'` … `EOF`, one simple call per file, never `Write`/`Edit` outside the worktree. In the clone (enricher, QA mode `code`) the same heredoc, from the first try: the runtime refuses a subagent's `Write` of a `.md` ("Subagents should return findings as text, not write report files": `ANALYSIS.md` and the code QA output in 7 runs of 2026-11; `PLAN.md` and lane files only sometimes pass), and a refused `Write` costs the whole file twice. `Edit` of a file that already exists there passed in those runs. Heredoc also refused: the content goes in your final answer, marked with the destination path, and the orchestrator writes it. The board is written only through `board.sh` (§ Scripts).

The rule in one line: a file **inside** the worktree = `Write`/`Edit`, never a heredoc (the guard refused heredocs inside the worktree inconsistently in 5 lanes of a 2026-11-09 run, Claude Code 2.1.319); a file **outside** it, or any `.impl/<slug>/*.md` written from the clone = heredoc through Bash, never `Write`.

## Bash in the agent worktree

The same guard refuses the command it cannot verify ("too complex to verify"). Refused (seen in the test drives, Claude Code 2.1.312 and 2.1.319):

- a compound command that mentions `git`, and `$(…)` substitution;
- an environment variable in front of the command (`HOME=<folder> command`, `VAR=x command`) and `env …` (`env -u VAR command`);
- a heredoc or program assembled on the fly for an interpreter (`python3 - <<'EOF'`, `python3 -c "$var"`), and a test with a computed operand;
- a loop (`for`, `while`), a long script in a single call, `cd` outside the worktree;
- a relative `git -C .` (the path counts as computed: always the absolute worktree path), and a compound that writes inside the worktree from a file outside it (`cp`/`cat` from the scratchpad).

One simple command per call; `git -C <worktree> reset --hard <hash>` in its own call; a value from another command (date, hash) = run it first and paste the literal result; a script of more than one line = a file inside the worktree written with `Write`, outside the commit, run by name. A heredoc (`cat > file <<'EOF'`) only for a path outside the worktree (§ Files outside the worktree); inside it, `Write`/`Edit`, an append included (`cat >> file <<'EOF'` passes in some runs and is refused in others). A large contiguous removal: print the two boundary lines (`sed -n '<a>p;<b>p' <file>`), then `sed -i '<a>,<b>d' <file>`, each in its own call. A command that only passes outside the worktree (Acceptance marked "clone only" in the lane): do not insist; a `WARNING` line on the board and the orchestrator runs it (`LANES.md` §3, step 1). Whatever else the guard refuses in this repo: profile § Worktree commands.

## Disposable service

The command is the output of `profile_run.sh service <worktree> --port <port> --slug <slug>-<port> --print` (your port, a disposable state named `<slug>-<port>`), run at the worktree root in the background (`run_in_background`); ready when `profile_run.sh health <worktree> --port <port> --slug <slug>-<port>` exits 0. `PROFILE_RUN FAILED` (profile from before § Commands): the prose of profile § Disposable service, same port and state. The health key waits by itself (up to 20 s): no `sleep` before it. Stop it at the end (`kill <pid>` of the process you started), never with `pkill -f <text of the command>` (it matches the shell that runs it: exit 144, and the rest of the call does not run) and never started as `cmd &` with a pid file. After the `kill`, the background task ends with exit 137 (SIGKILL) and the notification says it failed: that is the normal end of a service you stopped, not a finding and not a red verdict; only an exit before your `kill` counts as a crash. Never the owner's data state.

## Tests and checks

The suite and the per-item typecheck through `profile_run.sh suite <worktree>` / `profile_run.sh typecheck <worktree>`: it runs with no pipe and keeps the exit code, which is the verdict. The other checks and the area tests from profile § Checks and § Tests, output always filtered: with a pipe (`| tail`, `| grep`) the exit is the filter's, so run the runner's quiet mode without a pipe, or put `set -o pipefail` in front. Test choice per item: localized change = the area test; contract = producer and consumer tests; shared infrastructure = tests of the dependent areas; the whole suite only at the end of the lane and in the final QA. Contract fixture: through profile § Contract, then the `git diff` of the fixture folder, field by field. A check that needs the page in a browser (layout at a width, a click path, a screenshot) in a repo with no screen test: `node ${CLAUDE_PLUGIN_ROOT}/skills/qa-visual/scripts/cdp.mjs <steps.json>` (steps and output in the header of the file; Node 22 and a Chromium), the steps file in `<root>/.impl/<slug>/proto/` or in the worktree outside the commit; never a driver written for the run.

## Navigation

`_common § Navigation`; CodeGraph: § Tools above. No index: `grep`/`Read` by snippet.
