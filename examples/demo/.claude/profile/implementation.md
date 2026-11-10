# Profile of /wh:implementation

Illustrative example: the demo has no code; the commands below only show the format of each section. In a real repo, each line comes from a source in the repo.

## Commands
build: `dotnet build --nologo -v q` [inferred]
suite: `dotnet test --nologo -v q` [inferred]
typecheck: `dotnet format --verify-no-changes` [inferred]
service: `ASPNETCORE_URLS=http://localhost:<port> DB_NAME=bakery-<slug>-<port> dotnet run --project src` [inferred]
health: `curl -sf localhost:<port>/health` [inferred]

## Build
`dotnet build --nologo -v q` (no new warning = green; verdict by the exit). [inferred]

## Tests
Area: `dotnet test --nologo -v q --filter "FullyQualifiedName~<filter>"`. [inferred]
Suite: `dotnet test --nologo -v q` (verdict by the exit; to read: `dotnet test 2>&1 | tail -30`). [inferred]
Acceptance of an item = the area test that only goes green with the item done; a new test when there is none.

## Checks
`dotnet format --verify-no-changes` (end of lane and final QA). [inferred]

## Disposable service
`ASPNETCORE_URLS=http://localhost:<port> DB_NAME=bakery-<slug>-<port> dotnet run --project src 2>&1 | tail -5`; ready when `curl -s localhost:<port>/health` answers `ok`; stop: `kill <pid>`. [inferred]

## Contract
DTOs in `src/*/Dto`, HTTP routes and the persisted format of `Order`. Fixture: snapshots in `tests/__snapshots__`, updated with `UPDATE_SNAPSHOTS=1 dotnet test` and reviewed through `git diff tests/__snapshots__`. [inferred]

## Union files
`src/Shared/ErrorCodes.cs` `src/Shared/Messages.cs` (append only). [inferred]

## Protected files
`CHANGELOG.md`, `docs/features/*`, `docs/GLOSSARY.md`, `.claude/profile/*`, `docs/reports/*`.

## Enricher reading
Always: `docs/features/README.md` and `docs/GLOSSARY.md`. When the task touches the area: the feature's file. Before any grep: `codegraph explore`.

## Visual or e2e QA
—

## Closing docs
Changelog: `CHANGELOG.md`. Feature map: `/wh:feature-docs`. Glossary: `docs/GLOSSARY.md`. Open items: —. Conventions: —.

## Report
`docs/reports/<date>-<slug>.md`

## Models
—

## Worktree commands
—
