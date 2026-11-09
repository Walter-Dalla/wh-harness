---
id: P-007
status: open
created: 2026-11-09
related: [P-003]
---

# intake.sh reads the pending folder before impl_env.sh pulls main

## Problem
Phase 1 runs `intake.sh` before `impl_env.sh` (the slug comes from the pending file), and `impl_env.sh` does the `git pull --ff-only`. A pending file added or closed on the remote since the last pull is not seen by the intake (QA-wiring-05, low).

## Strategy
1. `SKILL.md` § 1: `git pull --ff-only` (or `impl_env.sh --pull-only`) before `intake.sh`, then `impl_env.sh <slug> --no-pull`.
2. Or `intake.sh` reads the folder at `<remote>/<main>` after a fetch.

## Locations
- `plugins/wh/skills/implementation/SKILL.md` (§ 1 Environment) — order of the two scripts.
- `plugins/wh/skills/implementation/scripts/impl_env.sh` — optional pull-only mode.

## Code references
- `plugins/wh/skills/implementation/scripts/impl_env.sh` — `--no-pull` flag already exists.

## Other references
- `docs/reports/2026-11-09-pending-intake.md` § Open items.

## Open questions
—
