# Profile of `/wh:implementation`: `.claude/profile/implementation.md`

What `/wh:implementation` and the `impl-*` agents need to know about the repository. The skill and the agents cite sections (`profile § Tests`), never commands. Clone, toolchain, git, ports, navigation, docs and limits live in `.claude/profile/_common.md` (template: `${CLAUDE_PLUGIN_ROOT}/skills/profile/COMMON.md`); here only what belongs to this skill. Generated and completed by the `profile` skill (`Skill(wh:profile, "implementation")`): sources in order, one line per fact with the source in brackets, `—` in a section with no answer (the phase that depends on it is skipped and the report says so).

## Template

```markdown
# Profile of /wh:implementation

## Commands
What the scripts run (`profile_run.sh <key>`): the five keys, one per line, the command in backticks and complete, `—` where the repo has none; the source in brackets after it. `<port>` and `<slug>` are replaced by the caller. No backtick inside a command (use `$(…)`).
build: `<command in quiet mode>`
suite: `<full command in quiet mode, no pipe>`
typecheck: `<lint or typecheck that runs per item>`
service: `<command that brings up the disposable service on <port>, state named with <slug>>`
health: `<command that exits 0 when the service on <port> answers>`

## Build
The `build` key of § Commands (no new warning = green). The verdict is this command's exit code: no pipe.

## Tests
Area: `<command with <filter>>` (e.g. `dotnet test X --filter "FullyQualifiedName~<filter>"`, `npm test -- <filter>`, `pytest -k <filter>`).
Suite: the `suite` key of § Commands (e.g. `dotnet test --nologo -v q`, `pytest -q`, `python3 -m unittest -q`). The verdict is this command's exit code: no pipe (`| grep` and `| tail` return the filter's exit). Filter only to read a long output, on a separate line: `<command> 2>&1 | tail -30`.
Acceptance of an item = the area test that only goes green with the item done (refactor: the area suite, green before and after); a new test when there is none. Clock and randomness injected where the repo injects them.

## Checks
Lint/typecheck/formatting/client verification, one per line, with the command and when it runs (per item, end of lane, final QA); the line that runs per item is the `typecheck` key of § Commands. E.g. `deploy/lint.sh` (final QA, without `--update`).

## Disposable service
The `service` key of § Commands brings up an isolated instance for testing (API, server, database) on `<port>`, its state named with `<slug>`; the `health` key says when it answers. Here: how to stop it and the state fixtures, if any. Ports: `_common § Ports`. `—` = the repo needs no service (both keys `—`).

## Contract
What counts as a contract (public API, DTO, event, persisted format, CLI, schema) and how the contract fixture is updated and reviewed (snapshot: acceptance variable and the `git diff` of the folder; golden file; generated schema). Producer and consumer tests.

## Union files
Files several lanes append lines to (constants, messages, translations, error codes, DI registration): append only; the orchestrator resolves them at merge. In backticks: `<glob>` `<glob>`.

## Protected files
What only the orchestrator edits (changelog, feature docs, conventions, `CLAUDE.md`, profiles, reports).

## Enricher reading
Which docs of `_common § Docs` the analysis always reads, which only when the task touches the area, and the code indexes to read before any grep.

## Visual or e2e QA
Skill or command that exercises the product end to end (e.g. `/wh:qa-visual <areas> --autonomous`, `npx playwright test`), what it needs (service on the final QA port, libs) and where it writes its report. `—` = skip.

## Closing docs
Where what the task changes or leaves open goes: changelog, feature status, owner's open items, conventions, glossary, feature map (skill), cleanup (skill). `—` for each one that does not exist.

## Report
Folder of the task reports (default `docs/reports/<date>-<slug>.md`).

## Models
The owner's rule for the model of each role (structurer, enricher, mechanical lane, structural lane, QA). `—` = the skill's default.

## Worktree commands
Learned from the runs: what the isolation guard refuses and the form that passes. `—` in the first profile; the retros add to it.
```
