---
name: qa-visual
description: Visual and functional QA of the client against an isolated local service: drives the product, reads screenshots and writes a bug report with evidence. Never fixes. Use for "run QA", "test visually".
---

# Visual and functional QA

Project profile (injected; `PROFILE_MISSING` = `Skill(wh:profile, "qa-visual")` and then `Read` both files, because the injection below ran before the profile existed):
!`cat .claude/profile/_common.md .claude/profile/qa-visual.md 2>/dev/null || echo PROFILE_MISSING`

Run the real product, exercise the features, take screenshots, **look at every screenshot** and deliver a bug report with evidence. **Nothing is fixed**: only found, reproduced, evidenced and documented.

## Input

`/wh:qa-visual [features…] [--res=WxH,…] [--lang=a,b] [--autonomous]`

| Argument | Default | Meaning |
|---|---|---|
| `features` | all the ones the status doc marks as done | names of the feature map files without `.md` |
| `--res` | profile § Input | resolutions (portrait has its own layout) |
| `--lang` | profile § Input | languages |
| `--autonomous` | on when there is no owner to answer (subagent) | the checkpoint (section 6) goes to the report instead of stopping |

## Output

Everything in `<root>/qa/` (`<root>` = the tested checkout: repository or worktree; already gitignored). Long round: prefer a worktree as `<root>` (another session may switch the main checkout's branch midway). Layout of screenshots, logs, data and scenarios: profile § Output. The round's scenarios survive the teardown in the folder the profile names; the next setup reinstalls them (retest).

## 0. Context

The docs of profile § Context (layer rules, feature map, status): the criteria for "correct" come from them. Without a mockup, the UI is judged by the rules in those docs, by the feature doc and by consistency across screens. Status says what exists: what it does not mark as done is not tested; known open items do not become new bugs. Code: `_common § Navigation`; without the index, a backend cause becomes a hypothesis.

## 1. Preparation

1. Feature map (index + files in scope) and status doc: build the **checklist** (profile § Checklist says how to read the screenshots and what is not a bug): per feature, expected behaviors with concrete numbers (timings, limits, prices, capacities), how to verify **on screen** and **in the backend**, status, and what requires level, currency or a long wait.
2. Client debug args (profile § Environment: where the canonical list is; they vary per branch).
3. Harness setup (profile § Harness). Note the configuration values it prints: they change flows.
4. QA service (profile § Harness), on the `_common § Ports` port; confirm with a real call.
5. Smoke: the smoke scenario of profile § Harness. Open the screenshot and describe it. A script error here is already a bug.

**Done when the checklist exists, the service responds and the smoke screenshot was read.**

## 2. How to test

- Scenario: ops, scripts and pitfalls in the harness doc (profile § Harness).
- **Action always tested through the UI**, with real input. Read-only queries to find coordinates are allowed.
- **Fixtures** (profile § Fixtures): building the starting state through the local API is allowed; the report records which scenario used which. What still requires a resource with no UI path becomes "Blocked (needs X)".
- **Clean user per scenario** (the harness creates one by default); the same id to chain scenarios.
- **Really wait**: wait ops by text/state; `sleep` only for animations.
- **Known pitfalls**: profile § Pitfalls, before blaming the product.
- **Time**: profile § Timings (shortest action, wait slack); an unfeasible wait = "Partial" item.
- **Backend**: state before and after every state-changing step, compared with the screen.

## 4. Rules

- One feature at a time; move on only with it documented in the report.
- Every bug reproduced **at least 2 times**; "reproduced N/M".
- Every bug has a screenshot and/or a log excerpt. No evidence, no entry.
- Bug, not implemented and intentional are different things. Not testable = "Blocked" with a reason; nothing skipped silently.
- One bug per cause: symptoms of the same root grouped.
- Writes only in `<root>/qa/` and the folders profile § Output lists (plus the local user state, which the teardown restores). Code, project, catalogs and snapshots stay as they are. **No commit.**
- `_common § Limits`: production and real MCPs never. A process the skill did not start stays alive.
- At the end, **always** the teardown of profile § Harness (even with the round broken midway), and `git status` with only what was there before.

## 5. Report (`qa/QA_REPORT.md`)

1. **Environment**: commit/branch, client/engine version, port, resolutions, languages, date, relevant configuration.
2. **Summary**: feature × status (OK / With bugs / Partial / Blocked / Not implemented) × bugs per severity, plus what was verified and worked (with the measured numbers).
3. **Bugs** (BUG-001…), by severity: feature, category (Asset / Map / UI / UX / Systemic), severity (Critical: freezes or prevents use; High: feature does not work; Medium: works with a defect; Low: cosmetic), resolution and language, steps (exact command, id, fixture), expected (citing the doc or the rule) vs. observed, reproduction N/M, evidence (screenshot and/or short log excerpt), probable cause marked as a hypothesis.
4. **Missing assets** (known placeholders apart).
5. **Not tested / partial** and why.
6. **Top 5 fixes**, in order, with the reason.
7. **Retest**: the command for each bug and where the scenarios are.
8. **Harness improvements**: ops that were missing, recurring false suspicions, new pitfalls (candidates for profile § Pitfalls).

What has to survive the round becomes a line in the open-items doc of profile § Open items (no new open-items file); a fix plan is temporary.

## 6. Checkpoint

Before testing the features: the checklist (section 1), the scenario plan (files, fixtures, chained ids) and the smoke (service responding and a real screenshot, opened and described). Interactive: show and wait for the OK. `--autonomous`: in a section of the report, and go on.
