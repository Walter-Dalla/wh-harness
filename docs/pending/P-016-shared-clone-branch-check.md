---
id: P-016
status: open
created: 2026-11-10
related: []
---

# Check ListAgents and the current branch before switching branch in a shared clone

## Problem
Owner (play-store retro): "regra em COMMON.md § Git / skill implementation: checar ListAgents e git branch --show-current antes de trocar de branch num clone compartilhado (o orquestrador deu git checkout main e desviou merge de outra sessão)."

## Strategy
1. Before implementing: validate against the current main (0.8.0). Partly covered already: `COMMON.md § Git` asks for `git branch --show-current` before committing, and `SKILL.md § 3` forbids `git switch`/merge/commit on the clone's checkout. Decide what is still missing (ListAgents, "before switching") or drop with justification.
2. Rule in `COMMON.md § Git` and/or the implementation skill: check `ListAgents` and `git branch --show-current` before changing branch in a shared clone.

## Locations
- `plugins/wh/skills/profile/COMMON.md:15` (§ Git) — "Checkout shared with other sessions: `git branch --show-current` before committing." [code plugins/wh/skills/profile/COMMON.md:15]
- `plugins/wh/skills/implementation/SKILL.md:63` (§ 3 Integration worktree) — "you never `git switch`, merge or commit on it" [code plugins/wh/skills/implementation/SKILL.md:63]
- `plugins/wh/skills/implementation/SKILL.md:34` (§ 1 Environment) — candidate for the pre-check [inferred]
- `plugins/wh/skills/implementation/scripts/impl_env.sh` — refuses a clone on the wrong branch (test `test_impl_env_refuses_dirty_clone_wrong_branch_and_bad_slug`) [code tests/test_scripts.py:294]

## Code references
- `test_impl_env_refuses_dirty_clone_wrong_branch_and_bad_slug` `tests/test_scripts.py:294` [code tests/test_scripts.py:294]

## Other references
- Play-store run retro (outside this repo) [inferred].

## Open questions
- Is `ListAgents` a tool the orchestrator has in every session (name and availability)?
- Where did the `git checkout main` happen given SKILL.md:63 already forbids it — a phase not covered (e.g. close/cleanup)?
