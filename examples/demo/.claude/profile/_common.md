# Common profile

## Clone
— (the current checkout) [inferred]

## Toolchain
Build and test: native `dotnet`; local HTTP: `curl`; kill a process: `kill <pid>`. [inferred]

## Git
Main branch: `main`. PR remote: `origin`. Protected: `main`. [inferred]

## Ports
The owner's: `5000`. Range for the `/wh:implementation` agents: `5100–5105`. Visual/e2e QA: from `5108` up. [inferred]

## Navigation
`.codegraph/` present (C#): `codegraph explore -p . "<symbols or question>"` (worktree: `codegraph init -y .` once; `codegraph sync .` after editing). Docs and configs: `grep`/`Read`. [context.json]

## Docs
`docs/GLOSSARY.md` — glossary (business × code × terms to avoid). [context.json]
`docs/features/README.md` — index of the feature map; one file per feature beside it. [context.json]

## Limits
No agent touches production, secrets, port `5000` or files outside the repo and the scratchpad. [inferred]
