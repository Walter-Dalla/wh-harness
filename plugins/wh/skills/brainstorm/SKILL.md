---
name: brainstorm
description: Product/design ideas for the current repository, anchored in its state and roadmap, in a draft note outside git.
disable-model-invocation: true
---

# Brainstorm

Project profile (injected; `PROFILE_MISSING` = `Skill(wh:profile, "brainstorm")` and then `Read` both files, because the injection below ran before the profile existed):
!`cat .claude/profile/_common.md .claude/profile/brainstorm.md 2>/dev/null || echo PROFILE_MISSING`

Output: a draft note with ideas for the owner to decide on, in the language of the repo's docs, not code. Code, feature status and `docs/` stay as they are. Promoting an idea to work is another step (the owner decides; then the status doc and `/wh:feature-docs`).

## 1. Frame

From the request: **topic** (feature, tension, phase or "open"), **horizon** (next step / next phase / long term) and given constraints (effort, platform, monetization). No topic: the open items of the roadmap (step 2). Ask only if the topic wavers between two very different areas; otherwise state the premise in the answer and go on.

## 2. Orient

Read in the order of the table in profile § Sources and stop when you understand the area: headings first (`grep -n '^#' <file>`), then only the sections that matter. Budget: 6–10 reads before generating. Technical rule docs (`_common § Docs`): once, only when an idea depends on a code rule. To know whether something already exists: `_common § Navigation` by name, never a whole service "for context". What the owner said in this conversation about the future outranks the docs; say when they diverge.

**Done when you know what exists, what is planned and which decisions were already taken on the topic.**

## 3. Diverge

12–20 raw ideas before judging any, rotating the lenses of profile § Lenses so they do not all come from the same angle.

## 4. Converge

Out, or reworked, the idea that breaks a constraint of profile § Constraints; duplicates merged; 5–8 remain. Already exists (step 2)? Partly = an extension of that feature, not a new feature.

## 5. Write the note

Folder, name and link format: profile § Note. Same topic on the same day = update the existing note.

```markdown
---
tags: [brainstorm, draft]
status: draft
date: YYYY-MM-DD
topic: <topic>
horizon: <next step | next phase | long term>
sources: [<the ones you read, in the profile's link format>]
---

# Brainstorm — <topic>

<One line: topic, horizon, premises (and where what the owner said diverges from the docs).>

## Ideas

### <n>. <Short name> — <one-sentence pitch, from the user's point of view>
- **Why:** <pillar, tension or id it resolves, with link>
- **How it fits:** <features touched, with link; what goes in and out; what the system has to derive>
- **Effort:** S/M/L — <layers touched>
- **Risks / questions:** <balancing, scale, owner decision, missing information>
- **First step:** <the smallest experiment that validates the idea>

## Prioritization
<table: idea × impact × effort × dependencies, in the order of your recommendation>

## Recommendation
<the 1–2 ideas to do first and why, one short paragraph>

## Decisions for the owner
- [ ] <question only the owner answers> — unblocks <ideas>

## Discarded
- <idea> — <constraint from step 4 that it breaks> (one line each)
```

What you inferred without looking at the code gets *(to verify)*.

## 6. Report

In the chat: path of the note, the recommendation in two or three lines and the open decisions. Confirm it is outside git (`git check-ignore -v <file>`).
