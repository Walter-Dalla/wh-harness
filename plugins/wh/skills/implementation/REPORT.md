# Retros and report of `/wh:implementation`

## Retro (each lane and the orchestrator)

`Skill(wh:retro, "file: <path>")` about your own session, from memory (without rereading large logs). The skill's "present to the user" step becomes the file `<root>/.impl/<slug>/retros/<lane|orchestrator>.md` (≤ 40 lines, ≤ 6 candidates); no proposal is applied. Agent in a worktree: the file is written through Bash with a heredoc (`ENVIRONMENT.md` § Files outside the worktree).

```markdown
# Retro · <lane> · <date>
| # | Severity | Category | Evidence (what happened, command/file) | Proposal (file and change) | Who applies (repo / owner, outside the repo) |
```

## Report (profile § Report, default `docs/reports/<date>-<slug>.md`, orchestrator only)

Sources: the lane reports, the board (`HUMAN`, `WARNING`, `END` with each lane's state), the retros, the phase 4 validation, the merge conflicts you resolved and the QA reports (`qa/<lane|code>.md`, `qa/final.md` and the retests) and the consultations (`agent_chat/`). Each line says what, where (file/symbol or command) and what is already done; an owner action comes with the command or text ready.

```markdown
# <title> · <date> · impl/<slug> · <PR on GitHub | no PR>
Enriched request (3 lines). Lanes: <lane: items, commits>. No PR: the merge command of phase 6.5.

## Errors
Remaining test, check or lint failures, merge conflicts and how they were resolved, fixes made at integration.

## Open items
Skipped or partial items and why; HUMAN lines; decisions taken without the owner (question, adopted option, alternative) and unconfirmed `[inferred]` profile lines; contracts that changed (fields) and what needs a joint deploy; scenarios for the profile's visual/e2e QA; profile sections left `—` and the phase that skipped. Each item line ends with the pending file id it became (`→ P-NNN`).

## Consultations
One line per file of `<root>/.impl/<slug>/agent_chat/`: `<lane> <item> · <question, short> · <answer, short> · impact <impact> · <who answered>`. Those that ended in `OWNER:` or `replan` also became pending files (§ Open items).

## QA
Decisions contested by the code QA (decision, objection, outcome); findings of the code QA and of the visual/e2e QA: fixed (commit) / retested / recorded (why). Deeper review, only if the owner wants it and only with a PR: `/code-review ultra <PR number>` (multi-agent in the cloud, billed). The PR number is born in phase 6.5, after this file: the ready command goes in the final answer. Without a PR, this section does not mention `ultra`. No agent or subagent triggers `ultra` or proposes it as an agent's next step.

## Problems found
Findings out of scope (bugs, neighboring debts), each with evidence.

## Cost
The table `agent_cost.py` prints (tokens per agent and model, with each one's share of the weighted tokens; not dollars), and one line naming the heaviest agent. "Not measured" and the reason when the script failed.

## Consolidated retro
| # | Severity | Category | Evidence (lanes) | Proposal | Who applies |
Candidates from all retros, deduplicated (the same problem in several lanes = one line citing all), by severity.
```

The report only records: fixes are left to the owner, except the profile line that phase 6.2 (`CLOSE.md`, step 2) says to apply.
