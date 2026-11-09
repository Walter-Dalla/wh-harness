---
name: feature-docs
description: Creates or updates the repository's feature map (index + one file per feature, interactions in sync). Use when a feature is born, changes or leaves.
---

# Feature map

Project profile (injected; `PROFILE_MISSING` = `Skill(wh:profile, "feature-docs")` and then `Read` both files, because the injection below ran before the profile existed):
!`cat .claude/profile/_common.md .claude/profile/feature-docs.md 2>/dev/null || echo PROFILE_MISSING`

The map is an on-demand dictionary for agents: an index + one file per feature (profile § Folder). Agents read the index and only the file they need, so each file stays short, exact and self-contained. Language and format: profile § Format.

The map describes **behavior**: flow, rules, who owns each rule. Where the code lives stays with the code (`_common § Navigation`): no "Code"/"Endpoints" section, no list of files or routes (they rot silently). A class, function or constant appears only inline, when it owns a rule an agent needs to find.

## 1. Understand the input

New, changed or removed feature; diff; commit range; or description. Only a topic: find out what changed (`git diff`, `git log`, changelog, feature status). Read the index; not the other files yet.

## 2. Categorize

Compare with the index table (ids, keywords, services) and decide:

- **Existing file** (the default): the input changes a rule, flow, endpoint or dependency of a listed feature, or adds a variation of it.
- **New file**: only when the input has its own user loop **and** its own owner in the code (service/entity/endpoints or panel). A helper, rule or new field is never a new file.
- **Several files**: cross-cutting change; the owning file in full and only the "Interactions" line of the affected ones.
- **Removal**: the section/file leaves with every link and index line that pointed at it.

Two equally plausible files, or a new file that would split an existing one: ask before writing. Then read the target files and the "Interactions" neighbors the change touches.

**Done when each part of the input has a target file and a category.**

## 3. Gather facts from the code

Every claim comes from code opened now, not from memory nor from the request text, per layer (profile § Layers): the flow and the rules with the owner of each; calls to other features and from them; what the user sees in the client; numbers citing the constant, with the value only when it explains the behavior.

**Done when every rule you are about to write has its owning symbol read.**

## 4. Write

File template: profile § Template (20–50 lines; cut detail before exceeding). Rules:

- **Single source.** A cross-cutting rule lives in the rule docs of profile § Rule sources: point at the section instead of copying. A rule of one feature lives only in `## Invariants` of its file; moving it there from the cross-cutting doc is the normal path. Status and roadmap in the status doc; history in the changelog. The map describes only the current state: no "it used to be".
- **Interactions on both sides.** A dependency created or removed in A also appears in B's "Interactions".
- **Index** in sync: profile § Index says which parts (table, who calls whom, diagram, currencies) and when each one changes.
- File name: profile § Format. Renaming = fix every link (grep).

## 5. Verify

The commands of profile § Verification. Done when: all exit 0 with no `MISSING`/`NO-PROPERTIES` line; every file within the profile's limit; every cited symbol you did not open in step 3 exists (grep); no "Code"/"Endpoints" section nor list of files or routes.

## 6. Report

Which files changed and why the input went there (the categorization), and what could not be confirmed in the code. Commit only if asked.
