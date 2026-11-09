# Triage and plan of `/wh:implementation`

The enricher applies this in the `plan` stage; the orchestrator checks it.

## Triage

| Size | Signal | Execution |
|---|---|---|
| **small** | one layer, or a contract with a small consumer; ≤ ~8 files | the orchestrator, inline (phase 3 of `SKILL.md`) |
| **large** | several layers joined by a contract, > ~8 files, or independent blocks that run in parallel | `impl-dev` lanes (`LANES.md` §1) |

Beyond size, the **risk**: a contract used by several consumers, a persisted format, the product's critical path or concurrency weigh toward large even with few files, because they earn their own lane, QA per lane and the consumer in a separate wave. Parallelizing only pays off with truly independent blocks; without them, one lane or inline. In doubt between the two with low risk, small: inline is cheaper.

## Plan

`<root>/.impl/<slug>/PLAN.md`:

```markdown
# <title> · <date>
Request: <the owner's, one line>. Enriched: <what it means in the product and in the code, 3–5 lines>. Analysis: ANALYSIS.md.
Decisions: <the owner's answers and the enricher's, with the why; "(no owner)" on the one the orchestrator adopted without asking>.
| Id | Item | Files (symbol) | Type (internal/contract) | Acceptance (command) |
```

Id = `<slug>-N`, in dependency order: contract producer before consumer, refactor before the feature that touches the same code, bug fix and refactor as separate items. Type **contract** = changes an interface between parts (API, DTO, event, persisted format, CLI); the rest is **internal**. Acceptance = one command that only goes green with the item done; a refactor item (same behavior): the area suite, green before and after. Large: plus the wave table of `LANES.md` §1.
