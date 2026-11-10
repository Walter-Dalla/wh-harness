---
id: P-023
status: open
created: 2026-11-10
related: [P-014]
---

# new_names.py: declarations it misses and the triple-quote heuristic

## Problem
`plugins/wh/skills/implementation/scripts/new_names.py` (QA gate 3 input, "declared names only" since run wh-pendencias) uses line regexes:
1. Fields and methods declared with no `=` or keyword are not listed: TS/Go/Java/C# fields (`foo: string;`, `private String foo;`), `public void bar()`, Python dataclass fields (QA-inventory-04). Gate 3 judges exactly those names in typed languages.
2. A `"""`/`'''` inside a one-line string literal flips the docstring tracking, so every later line of that file is read the wrong way (seen on `new_names.py` itself: its declarations after line 36 are missing).
3. A last keyword argument alone on a continuation line (`timeout=5` before a lone `)`) is listed (QA-inventory-05).
4. Unpacking (`a, b = …`) and destructuring (`const { a } = …`) declare nothing to it.
5. Since QA-final-03 an `=` right after an operator character is refused, so a type ending in one with no space before `=` (`f: Map<K,V>= …`) is missed.

## Strategy
1. Per-language tokenizing for the languages a profile declares (Python: `tokenize`/`ast` on the new file at `<ref>`; others: a typed-member regex `^\s*MODIFIERS? TYPE NAME[;=(]`).
2. Replace the triple-quote toggle with string-aware scanning (or `tokenize` for `.py`).
3. Tests per case above in `tests/test_new_names.py`.
Alternative: keep regexes and only document the limits (already done in `impl-qa.md` gate 3).

## Locations
- `plugins/wh/skills/implementation/scripts/new_names.py` (`code_part`, `declared`, `KEYWORD_DECL`, `ASSIGN_DECL`) — detection
- `tests/test_new_names.py` — cases
- `plugins/wh/agents/impl-qa.md` (gate 3) — limits text to update

## Code references
- `declared`, `code_part` `plugins/wh/skills/implementation/scripts/new_names.py` [inferred]

## Other references
- Report `docs/reports/2026-11-10-wh-pendencias.md` (QA-inventory-04, -05; inventory lane note on the triple quote).

## Open questions
- Is the regex approach with documented limits enough for the repos that use wh, or is a per-language tokenizer worth its cost?
