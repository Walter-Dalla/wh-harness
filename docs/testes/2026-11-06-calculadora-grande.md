# Test drive 2 · calculadora, large task · 2026-11-06

Second end-to-end run of `/wh:implementation`, now on plugin `wh` 0.6.0 (uncommitted working tree, Claude Code 2.1.319), to cover what the 2026-10-28 test drive did not exercise: `impl-dev` lanes in worktrees, `BOARD.md`, `progress/`, `scope.sh`, queries, code QA per lane. One headless run (`run.sh 3 … --permission-mode bypassPermissions --dangerously-skip-permissions --model opus`) in `/home/walter/calc-harness-test`, from `main` (f846fe2), local bare remote, no owner.

Request: expression parser (precedence, parentheses, unary minus), history in a JSON file with a `history` subcommand, CLI accepting the whole expression, tests; with "Triage: large" in the request, to force lanes.

Logs (outside git): `/home/walter/calc-harness-logs/run-3/` (`session.jsonl`, `events.jsonl`, `impl-snapshot/`, `git/`, `analysis.txt`). Report the harness wrote: `calc-harness-test/docs/relatorios/2026-11-06-expr-hist.md`.

| Result | Time | Cost | Commits | Tests | Subagents |
|---|---|---|---|---|---|
| DONE, branch `impl/expr-hist` (0882c10) on the remote, no PR; 2 low bugs open, recorded | 33m58s | US$ 13.05 (opus 12.71 · sonnet 0.34) | 9 items + 5 QA fixes + 4 merges + report + docs; 9 files, +1093 −52 | 77 OK (were 16) | enrich; 3 `impl-dev` in worktrees (2 in wave 1, 1 in wave 2); 3 `impl-qa code` (sonnet, in the clone); `impl-qa final` + retest (opus, worktree) |

## What 0.6.0 solved (checked in the log)

| Item | Evidence |
|---|---|
| G1 no owner | No question in text; "Answers (no owner)" to the enricher; 10 decisions in the report's "Decisions taken without the owner" table, with the alternative |
| G2 files outside the worktree | Nothing lost: 10 retros, 3 checkpoints, 9 Acceptance logs, 5 QA outputs in `impl-snapshot/`, written by heredoc; folders created by the orchestrator before the enricher |
| N4 board without `$(…)` | Complete `BOARD.md`: `START`, 3 `CONTRACT`, 3 `WARNING`, `END` of each lane, the orchestrator's `WAVE` and `MERGE`; the agents ran `date -u` separately |
| G3 and N6 no PR | `gh repo view` in the first call of phase 1; report title with the branch and "no PR"; merge command in the report and in the answer |
| N5 absolute git | Agents used `/usr/bin/git -C <worktree>` taken from the `Commands:` line |
| N7 plugin root | The orchestrator called `scope.sh` and `preflight.sh` by the resolved path |
| N8 enricher cost | The enricher read `TRIAGE.md` and only § 1 of `LANES.md` (`sed`); no subagent read `SKILL.md` |
| G4 re-reading | The orchestrator read each auxiliary file once |
| G7 profile | Four profile sections updated in the report commit, marked "applied" in the consolidated retro |
| N16 cleanup | No worktree or `worktree-agent-*` branch at the end; `.impl/expr-hist/` deleted; clean `git status` |
| Contract in waves | Producers (`parser`, `historico`) in W1, consumer (`cli`) in W2 with the board's `CONTRACT` lines; `scope.sh` OK in all three lanes |
| QA | Code QA confirmed the decisions in the three lanes; final QA found 5 real bugs (full, closed, non-encodable stdout, 0444 file), fixed and retested; 2 came back in the single retest and went to the report |

## New gaps

All seven were applied in 0.6.1, the same day; none was checked by a new run.

| # | Sev. | Evidence | Proposal (harness file) |
|---|---|---|---|
| T1 | high | The worktree guard refuses more than `ENVIRONMENT.md` lists: 28 refusals in the run. `HOME=<temp> command` ("sets HOME, injecting git configuration"), `env -u VAR …`, heredoc to `python3`, `python3 -m unittest` with a computed operand, long script, loop, `cd` outside. Two lanes closed `PARTIAL` only because the Acceptance used `HOME=` | `ENVIRONMENT.md` § Bash in the agent worktree: widen the list (environment-variable prefix, `env`, heredoc to an interpreter, loop, `cd` outside). `LANES.md` § 1, Acceptance at the tip: an Acceptance that needs an environment variable or `HOME` gets the mark "clone only" and the orchestrator runs it, at merge |
| T2 | medium | `PARTIAL` because part of the Acceptance only runs outside the worktree is not a continuation case: the orchestrator ran the missing part in each lane's worktree and merged, against the new `LANES.md` § 3.1 ("`PARTIAL`: step 9") | `LANES.md` § 3.1: `PARTIAL` with all commits done and only verification pending = the orchestrator runs the verification and moves on; continuation only when an item is missing |
| T3 | medium | CLI risks only showed up in the final QA: standard output full, closed or non-encodable; user file read-only, mode, symlink; JSON with `true`, `NaN`, `1e999` | `impl-enrich.md`, risk list: a line for CLI (stdout and stderr full or closed, encoding) and, under "persisted format", the file that already exists (mode, read-only, symlink) and non-strict JSON |
| T4 | low | The final answer offered `/code-review ultra` without a number, although the no-PR mode says not to offer it | `SKILL.md` § 6.6: say "no PR, do not cite `ultra`" in the sentence itself |
| T5 | low | The enricher built a prototype in `/tmp/expr-hist-proto` (deleted later), outside the repo and `.impl/`, against `_common § Limits` | `impl-enrich.md`: a disposable prototype goes in `<repo>/.impl/<slug>/proto/` |
| T6 | low | A lane cites in a docstring a symbol another lane removes; the W2 Acceptance stayed red until the fix | `impl-enrich.md`: the lane file does not cite a symbol the plan removes; the wave query classifies each `grep` occurrence by owner |
| T7 | low | Acceptance log by heredoc forces the agent to recopy the output; a QA fix that widens `May touch` was done by hand; QA `code` did not know whether it could run the branch | `impl-dev.md`: log by simple redirection when the guard allows; `LANES.md` § 3.3: a fix that touches a new file updates the lane line; `impl-qa.md`: mode `code` runs nothing, said in the mode's first line |

## Not observed

Lane continuation by a new agent (N1; no lane stopped with an item to do), copying visual QA screenshots (N2; repo without visual QA), `FAILED` and `WAITING`, disposable service and ports, real GitHub with a PR, `/wh:cleanup` with a profile, CodeGraph. There was one `QUESTION` query (lane `cli`, authorized by the enricher, `WARNING` line on the board).

## Cost (G4b)

US$ 13.05 for 9 items in 3 lanes, against US$ 5.41 and 4.68 for the small runs (3 and 5 items, orchestrator on the most expensive model). Opus read 12.2M cache tokens across all agents together. The run does not separate cost per agent, so it does not give the fixed cost of a single lane: the G4b decision remains unmeasured. To measure it, repeat a small task with the same session in `--model opus`, inline, and compare with runs 1 and 2.
