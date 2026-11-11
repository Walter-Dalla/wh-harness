# Template for `.claude/profile/_common.md`

Facts every skill uses. Each line ends with its source in brackets. Section with no answer: `—`.

```markdown
# Common profile

## Clone
Where the session and the worktrees run (native toolchain) and what the other checkout is, if any. `—` = the current checkout.

## Toolchain
The commands that change per checkout or OS: build/test (`dotnet` vs `dotnet.exe`, `pnpm`…), local HTTP (`curl` vs `curl.exe`), Python, how to kill a process. How to reach localhost on the other side (WSL ↔ Windows).

## Git
Main branch: `main`. PR remote: `origin` (or the name that points at GitHub). Protected branches. Identity and push (e.g. `git -c user.name=…`, `git.exe push` when the credential lives on Windows). Checkout shared with other sessions: `git branch --show-current` before committing or switching branch; a checkout another session may be using is never switched (work in a worktree).

## Ports
The owner's (never used by a skill): e.g. `5000`. Range for the `/wh:implementation` agents (6 ports): e.g. `5100–5105`. Visual/e2e QA: e.g. from `5108` up (first free one; never kills what already sits on a port). The numbers are examples: put the repo's, with the source.

## Navigation
`.codegraph/` present and what it covers: `codegraph explore -p . "<symbols or question>"` (worktree: `codegraph init -y .` once; `codegraph sync .` after editing). What the index does not cover (languages, scenes, configs, docs): `grep`/`Read`. Client index, if any (e.g. `scripts/INDEX.md`).

## Docs
One per line, `path` — what it is: map (`CLAUDE.md`), layer rules that do not load on their own (`conventions.md`, `<client>/CLAUDE.md`), feature map (`docs/features/README.md`), status and debt (`FEATURES.md`), glossary, open items of the owner and of the agents, changelog, task reports, UI brief.

## Pending
Folder of the owner's pending items, one file per item in the format of `${CLAUDE_PLUGIN_ROOT}/skills/implementation/PENDING.md` (default `docs/pending/`; the intake script falls back to it when this section is absent). `—` = the default.

## Limits
What no agent touches: production (URL, server, SSH), real MCPs, the owner's ports and databases, files outside the repo and the scratchpad, secrets.
```
