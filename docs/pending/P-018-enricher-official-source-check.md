---
id: P-018
status: open
created: 2026-11-10
related: []
---

# Enricher checks the official page for a requirement that changes visible text

## Problem
Owner (play-store retro): "enricher confere na página oficial requisito que muda texto visível."

## Strategy
1. Before implementing: validate against the current main (0.8.0); drop with justification in the report if not.
2. Rule in the enricher: a requirement that changes visible text is checked against the official page (of the store/provider) before it enters the plan.

## Locations
- `plugins/wh/agents/impl-enrich.md:39` (§ Stage `analyze`) — "public or legal text (store, terms, policy): each asserted rule with the `file:symbol` that guarantees it" — neighbor rule to extend [code plugins/wh/agents/impl-enrich.md:39]
- `plugins/wh/agents/impl-enrich.md:34` — "state coming from outside (store, provider, webhook)" [code plugins/wh/agents/impl-enrich.md:34]
- `plugins/wh/agents/impl-enrich.md:4` (`tools:`) — no WebFetch today; how the enricher reaches the official page [code plugins/wh/agents/impl-enrich.md:4]
- `plugins/wh/agents/impl-enrich.md:20` (**Certainty**) — the source mark of a fetched page [code plugins/wh/agents/impl-enrich.md:20]

## Code references
—

## Other references
- Play-store run retro (outside this repo) [inferred].

## Open questions
- The enricher's tools are `Read, Write, Edit, Bash, Skill`: add `WebFetch`, or turn the check into an owner question with the official URL?
