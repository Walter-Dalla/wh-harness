---
name: implementation
description: Implements a task end to end in any repository: analysis and plan by an enricher, parallel lanes in worktrees, code QA and final QA, PR, retros and report.
disable-model-invocation: true
---

# Impl

Project profile (injected; `PROFILE_MISSING` = phase 1 writes the profile before going on):
!`cat .claude/profile/_common.md .claude/profile/implementation.md 2>/dev/null || echo PROFILE_MISSING`

You are the **orchestrator**, owner of the task from the request to the open PR. Phases, in order, each ending at the criterion in **bold**:

1. Environment
2. Enrich: the `impl-enrich` subagent does the technical analysis and the plan; it stays alive for the developers' consultations
3. Execute (small: you; large: `impl-dev` subagents, merged by you into `impl/<slug>`)
4. Code QA: static, per lane as soon as it finishes (decisions, standards, names, risks)
5. Final QA: the expensive run, once (suite, checks, visual or e2e QA if the repo has one, integration)
6. Close: retros, report, closing docs, cleanup, PR

What belongs to the repository (build, test and check commands, disposable service, union files, closing docs, limits) comes from the **profile** `.claude/profile/implementation.md` (format: [`PROFILE.md`](PROFILE.md)) and from `.claude/profile/_common.md` (clone, toolchain, git, ports, navigation, docs, limits), at the repo root. This skill and the agents never cite a project command: they cite the profile section.

Subagent tools (RTK, CodeGraph, when installed): [`ENVIRONMENT.md`](ENVIRONMENT.md) § Tools.

Plugin root: `${CLAUDE_PLUGIN_ROOT}`. In the files of this skill you open with `Read` (`LANES.md`, `ENVIRONMENT.md`, `REPORT.md`, `TRIAGE.md`) the variable `CLAUDE_PLUGIN_ROOT` appears unresolved: replace it with that path.

**Subagent files:** everything `impl-dev` and `impl-qa` write for the orchestrator (QA output, retro, checkpoint, board) goes to an **absolute** path in `<root>/.impl/<slug>/…` (outside git through the clone's exclude): an agent's worktree is removed when it ends with no change, and would take the files with it (to verify on each Claude Code version; the absolute path does not depend on it). Code and commits stay in the worktree. The board: appended through `printf … >>`. The worktree isolation guard refuses `Write`/`Edit` outside it (seen in Claude Code 2.1.312): the agent writes those files through Bash and you create the folders before dispatching it (phase 1); rule in [`ENVIRONMENT.md`](ENVIRONMENT.md) § Files outside the worktree.

Autonomy: straight to the commit and the PR. You ask the owner only in phase 2 (and on an `OWNER:` consultation that stops a lane); session without an owner (no `AskUserQuestion`): phase 2, step 2. A subagent's long output (diff, screenshots) stays in its files; you read the reports. Merging the PR belongs to the owner. This skill and each file of it you already read stay in your context: do not reread them in later phases.
**Subagent limit:** at most **3 subagents running at the same time** (`impl-dev` lanes and `impl-qa` QAs). The enricher idle between messages takes no slot; one of its turns (consultation, replan) does. A lane, code QA or final QA only dispatches when there is a slot; what does not fit waits, in plan order. Reason: API rate limit and the machine's CPU (parallel builds and tests). A skill that opens subagents (e.g. `/code-review` at a high level) takes the slots it opens: only you call it, with free slots; no subagent calls it.
**Subagent model:** the `model` of each `Agent(...)` comes from profile § Models (the owner's rule per role: enricher, mechanical lane, structural lane, QA); section `—` = `"opus"`, except the `code` QA (`"sonnet"`: it receives a ready diff and plan, low context pressure).
**Subagent effort:** never pass `effort` in `Agent(...)`, and no agent definition fixes `effort` in its frontmatter: each subagent runs at its model's default effort.

## 1. Environment

- The session opens at the repository root, in the clone `_common` § Clone names (no profile: the current one). A checkout without the native toolchain (e.g. `/mnt/c` on WSL with dotnet/node only on Windows): stop and tell the owner where to open `claude` and call `/wh:implementation` again. Reason: native builds and tests, fast I/O, and the agents' worktrees are born from the session's repository.
- Main branch and PR remote: `_common` § Git (default: `main` and `origin`). `git status` clean and on main; otherwise stop and say what is there. `git pull --ff-only`; `git ls-remote --heads <remote> <main>` must respond; if authentication fails, ask the owner for `! gh auth setup-git` and stop.
- Once per clone: `.impl/` and `.claude/worktrees/` in `.git/info/exclude`, one line each (`grep -qx` before `printf … >>`).
- **PR:** `gh repo view --json nameWithOwner` responds = PR on GitHub in phase 6. Failure (remote that is not GitHub, `gh` missing or not logged in) = **no-PR mode**, decided here: phase 6 delivers the branch on the remote and the merge command, and the report says so in its title.
- **Agents' git:** `command -v git` gives the binary's absolute path; it goes on the `Commands:` line of every agent prompt (a bare `git` may be rewritten by a wrapper, and the worktree guard refuses it).
- **Task folders:** define the `slug` (short, kebab-case) and create `<root>/.impl/<slug>/` with `qa/`, `retros/`, `progress/` and `acceptance/` (`mkdir -p`); a subagent in a worktree cannot create them.
- **Profile:** `.claude/profile/implementation.md` or `_common.md` missing or with a section short = `Skill(wh:profile, "implementation defer")` and then `Read` both files (the injection at the top ran before they existed); `defer` = the skill does not ask, the `[inferred]` lines enter the `AskUserQuestion` of phase 2, and the profile is the first commit of `impl/<slug>` (`chore: /wh:implementation profile`), before any lane.
- `.codegraph/` present: `codegraph sync .`.
- Ports, scripts, states, checkpoint and commands: [`ENVIRONMENT.md`](ENVIRONMENT.md).

**Done when the session is in the right clone, on the updated and clean main branch, the profile exists, the index (if any) is synced, the exclude has `.impl/` and `.claude/worktrees/`, the task folders are created, the PR mode is decided, and the remote responds.**

## 2. Enrich (technical analysis and plan)

The enricher is the `impl-enrich` subagent, the task's architect: it does the technical analysis, writes the plan and stays alive until the PR to answer the developers' questions. You bridge to the owner.

1. **Analyze:** `Agent(subagent_type: "wh:impl-enrich", model: <profile § Models; no rule, "opus">, prompt: "PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}. Stage: analyze. Repo: <absolute root>. Profile: <root>/.claude/profile/implementation.md and _common.md. Slug: <slug>. Request: <the owner's, verbatim>. prompt-graph context: <the `[wh:prompt-graph]` block that came with the request, or —>.")`, without `isolation` (it only reads the repo and writes in `.impl/<slug>/`) and without `name`. **Keep the agent id**: every later stage resumes it through `SendMessage`, with the analysis in its memory.
2. **Questions:** a `QUESTIONS` answer = `AskUserQuestion` with all of them, in the options it brought (plus the profile confirmation, if you wrote it); the tool accepts up to 4 questions per call, 2–4 options each: beyond that, calls in sequence, the profile ones grouped by section. Relay the answers through `SendMessage` with "Stage: plan. Answers: …"; `NO QUESTIONS` = send "Stage: plan" directly. **No owner** (the `AskUserQuestion` tool does not exist in the session, e.g. headless `-p`): do not stop and do not ask in text. Adopt the recommended option (the first) of each question and relay "Stage: plan. Answers (no owner): …"; the enricher marks each one with `(no owner)` in the plan's Decisions, and the profile's `[inferred]` lines stay unconfirmed. Each one enters the report's Open items ("Decisions taken without the owner": question, adopted option, alternative) and the final answer.
3. **Check:** read `ANALYSIS.md` and `PLAN.md`. An item without file, symbol, type or executable Acceptance, a design choice without its why, or a decision resting only on an `inferred` claim, goes back to it in a message.

Triage (small = you, inline, in phase 3; large = `impl-dev` lanes) and the format of `<root>/.impl/<slug>/PLAN.md` (ids `<slug>-N`, type internal or contract, Acceptance): [`TRIAGE.md`](TRIAGE.md). The enricher applies it; you read the file once, to check the plan.

**Consultations during the task:** a question the lane file, `ANALYSIS.md` or `PLAN.md` already answers, whose answer changes no other lane nor contract, you answer directly (citing the passage). The rest: an `impl-dev` (or you, on a small task, or an `impl-qa` with a decision to confirm) with a doubt about a rule or direction sends `QUESTION <lane> <item>: …`. Relay it to the enricher (`SendMessage` with "Stage: consult." + the message) and return the answer to whoever asked (`SendMessage` to their id). The enricher answers with the **impact** (item / lane / other lanes / contract / replan): `other lanes` or `contract` = notify the cited lanes (`SendMessage`) with the updated lane file; `replan` = stop dispatching new lanes until it updates the plan. `OWNER:` = ask the owner only if the lane is stopped on it; otherwise (and always, in a session without an owner), follow the enricher's recommendation and record it as an open item of the report. After a session restart, the enricher died with it: never count the old id as alive; answer yourself from `ANALYSIS.md` and `PLAN.md` and note each answer in the Decisions of `PLAN.md` as "orchestrator decision", or dispatch a new `impl-enrich` with "Stage: consult" when the doubt calls for analysis.

**Done when every owner question is answered, `ANALYSIS.md` has architecture, technical files and a proposal with the why, and every plan item has file, symbol, type and executable Acceptance (and, if large, lane, wave and estimate).**

## 3. Execute

Integration branch: `git switch -c impl/<slug> <main>` (new profile: its commit here).

Large: [`LANES.md`](LANES.md) §2–3 (includes phase 4 for each lane), then phase 5.

Small, item by item:
1. One item at a time: edit the minimum of the current item, without getting ahead on the next; the rules of the repo's `CLAUDE.md`/`AGENTS.md` and of the rule docs of profile § Enricher reading hold for every item.
2. Run the Acceptance; the item does not close red.
3. An **internal** item changes neither contract nor contract fixture (snapshot, golden, schema): if it did, you changed the contract, fix the code. A **contract** item: producer and consumer tests, fixture updated through profile § Contract and reviewed field by field, consumer in the same plan.
4. `git diff --stat` before the commit: only the item's files. Commit with the message starting with the id (`<slug>-2: …`) and the co-authorship line; `git push -u <remote> impl/<slug>`. Two items that came out together in the same passage: one commit with both ids (`<slug>-1 <slug>-2: …`); never rewrite history to separate them.
5. `codegraph sync .` if the repo has an index.

A neighboring problem outside the request goes to the report's findings; the code stays in scope.

**Done when every item has a commit on the remote and evidence of a green Acceptance ([`ENVIRONMENT.md`](ENVIRONMENT.md) § States).**

## 4. Code QA (static, as soon as the code is ready)

A review without running anything, by an `impl-qa` with fresh eyes: plan decisions, the repo's implementation standards, names (the profile's glossary, if any) and risks. No `/code-review`: it spends too much for what it finds.

- Large: one per lane, as soon as it delivers, before the merge ([`LANES.md`](LANES.md) §3).
- Small: no separate code QA; the final QA (phase 5, `Gates: yes`) applies the four gates to the whole diff and you fix the findings (step below). Exception: a **contract** item whose consumer is outside the plan (another repository, an already published client, a persisted format an old version reads) = one code QA on `impl/<slug>` (base `<main>`; `<lane>` = `code` in the template below) right after the item, as in the large case; a contract with producer and consumer in the same plan waits for the final QA.

Before dispatching, write the diff: `git diff <base>...<remote>/<branch> > <root>/.impl/<slug>/qa/<lane>.diff`.

```text
PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}
Mode: code. Task: <slug>. Repo: <root>. Profile: <root>/.claude/profile/implementation.md and _common.md. Plan: <root>/.impl/<slug>/PLAN.md. Lane: <<root>/.impl/<slug>/<lane>.md | "all">.
Branch: <impl/<slug>-<lane> | impl/<slug>> @ <hash>. Diff base: <base hash>. Remote: <remote>. Diff: <root>/.impl/<slug>/qa/<lane>.diff.
Output: <root>/.impl/<slug>/qa/<lane>.md. Retro: <root>/.impl/<slug>/retros/qa-<lane>.md.
Commands: git = <absolute path from phase 1> -C <root> …, one command per call.
Retest: <"no" | ids of the fixed findings>.
```

`Agent(subagent_type: "wh:impl-qa", model: <profile § Models; no rule, "sonnet">, prompt: …)`, **without `isolation`** (static review: it reads the diff in the clone, with no reset nor new index) and without `name`.

Findings (type and severity in the QA file): **bug, standard, name or missing test** = fix (one commit per finding, `QA-<lane>-NN: …`), critical and high first. Then **one** retest by `impl-qa` only when there was a critical, high or medium code finding, covering those ids and the open ones in the same area (a fix may change the neighbor's conditions); a fix of low severity only, or of a test only, you check by running the item's Acceptance. What comes back goes to the report. A critical or high finding fixed after that retest gets a short retest of the id only, or enters the `Verify:` of the final QA prompt. **Undemonstrated risk, contested decision or product judgment** = report, no code; a risk the QA measured or reproduced counts as a bug. Output or retro the QA returned in its answer (write refused): you write them to the paths from the prompt.

**Done when every finding is fixed and retested, or recorded for the report.**

## 5. Final QA (the expensive run, once, at the tip of `impl/<slug>`)

Push `impl/<slug>` and one `impl-qa` in mode `final`:

```text
PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}
Mode: final. Task: <slug>. Repo: <root>. Profile: <root>/.claude/profile/implementation.md and _common.md. Plan: <root>/.impl/<slug>/PLAN.md.
Branch: impl/<slug> @ <hash>. Diff base: <main>. Remote: <remote>. Touched areas: <visible features/modules, or "none">.
Output: <root>/.impl/<slug>/qa/final.md. Retro: <root>/.impl/<slug>/retros/qa-final.md.
Commands: profile § Worktree commands before the 1st command; git = <absolute path from phase 1> -C <worktree> …, one command per call.
Retest: <"no" | ids of the fixed findings>.
Verify: <"—" | critical or high ids of phase 4 fixed without retest>.
Gates: <yes (small task: the four gates of mode code over the whole diff) | no>.
```

`Agent(subagent_type: "wh:impl-qa", isolation: "worktree", model: <profile § Models; no rule, "opus">, prompt: …)`, without `name`.

It runs the profile's suite and checks, reviews the integration commits and the seams between lanes, and runs the profile's visual or e2e QA on the touched areas (only when what the user sees changed). In parallel you check what is cheap: the profile's build with no new warning, the profile's lint, `git status` with no received fixture nor junk.

Findings: the same triage as phase 4, retest included; a bug across many areas becomes a FIX `impl-dev` lane (`LANES.md` §2–3). After the fixes, **one** retest (`Retest: <ids>`); what comes back goes to the report. API quota near its end: retest only the critical and high findings, and visual/e2e QA only on the areas of contract items.

**Done when the profile's suite and checks are green at the tip of `impl/<slug>` and every finding is fixed and retested, or recorded for the report.**

## 6. Close

1. **Retros:** send the enricher "Stage: retro. File: <root>/.impl/<slug>/retros/enricher.md". **Your retro:** `Skill(wh:retro, "file: <root>/.impl/<slug>/retros/orchestrator.md")` about this session, in the format of [`REPORT.md`](REPORT.md).
2. **Report:** gather the retros and write the report to the path of profile § Report by [`REPORT.md`](REPORT.md); commit `docs: report <slug>`. A candidate of any severity whose proposal is one line of `.claude/profile/*.md` (e.g. § Worktree commands, § Tests): apply it in the same commit and mark "applied" in the consolidated retro (the profile belongs to the repo; the owner reviews the line in the PR). `CLAUDE.md`, rule docs and everything else: the owner only (question in the final answer). A screenshot that proves a still-open bug: copy it from `<root>/.impl/<slug>/qa/visual/` to a folder `<date>-<slug>/` beside the report, before the cleanup deletes `.impl/`.
3. **Closing docs** (profile § Closing docs: changelog, feature map, open items, glossary, conventions), commit `docs: <slug>`, with the "notes for the docs" from the lane reports at hand. An open item (debt, owner decision, new convention, new term) goes to the doc the profile names; with no doc for it, it stays in the report.
4. **Cleanup:** `Skill(wh:cleanup, "<slug>")` when `.claude/profile/cleanup.md` exists (executed files, open items, `.md` files that cite changed code, worktrees); without it, the minimum inline: delete `<root>/.impl/<slug>/` (already consolidated in the report) and any plan or prompt `.md` the task created inside the repo; a repo `.md` that cites changed code (name, path, route) is updated; `git worktree remove` of the task's worktrees that still exist (`git worktree list --porcelain`): those on branch `impl/<slug>-*` and the agent ones (`worktree-agent-*`) whose HEAD is a commit of `<main>..impl/<slug>`; then `git branch -D` of those `worktree-agent-*` (the `impl/<slug>-*` ones stay on the remote until the PR). Another session's worktree stays.
5. **Push and PR:** `git push -u <remote> impl/<slug>`; `gh pr create --base <main> --head impl/<slug>`, body = summary of the report (≤ 20 lines) + link to the file + the attribution footer. No-PR mode (phase 1): push only; the report and the answer carry the merge command (`git switch <main> && git merge --no-ff impl/<slug> && git push <remote> <main>`).
6. **Answer to the owner** (≤ 10 lines): PR link (or the branch and the merge command), closed items, open items only they resolve (with the decisions taken without the owner), report path; with a PR, the command `/code-review ultra <PR number>` ready to paste; without a PR, do not mention `ultra` in any form.

**Done when the PR is open (no PR: the branch is on the remote) and the owner received the link or the merge command.**
