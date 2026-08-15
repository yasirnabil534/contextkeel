---
name: 00-core
description: Core protocol — read project context before code, defer to shared conventions
globs: 
always_apply: true
---
# Core Protocol

This repo's behavior is defined in shared, tool-agnostic files. Follow them so
output is consistent across IDEs and people.

## Before working
1. Read `project.yml` (stack, architecture, UI, conventions).
2. If `the code index`/`uv` are missing, run `ckeel doctor --fix` first (auto, don't ask).
3. Read code-structure context from **the code index** (`.contextkeel/index/REPORT.md`,
   `graph.json`) instead of scanning the whole repo — regenerate via
   `update-context` if missing/stale. This saves tokens.
4. Read prescriptive context from `Vault/Context/` (Conventions, Domain
   Glossary, API Contracts, Tech Stack).
5. Resolve any `auto`/empty `project.yml` field from manifests; fall back to its
   `defaults:` block. Never block on missing config.

## Given requirements for a new project/module/large feature
- **Plan before coding**: run the `write-prompt-plan` skill first. It writes
  phased, dependency-tracked prompt lists per tier to `.docs/` with a
  migration-style registry so multiple people can track progress without
  colliding. Only start implementing once asked to execute the plan.

## While working
- Follow `Vault/Context/Conventions.md` (canonical) and `AGENTS.md`.
- Apply language idioms from the matching `lang-*` rule.
- Keep changes small and focused.

## The context system is hybrid
- **the code index** (`.contextkeel/index/`, gitignored) owns architecture/module-map/code
  structure — it's generated, not authored. Regenerate it; never hand-edit it.
- **`Vault/`** owns prescriptive/human content (Conventions, Glossary, API
  Contracts, ADRs) — agent-maintained, human-optional. The user views it but
  does not edit it. Write notes as plain markdown; the the notes viewer app is not
  required. Substitute real values for `{{title}}`/`{{date}}`/`{{time}}` —
  never leave literal `{{...}}` tokens in a note.

## After meaningful changes
- New/changed module or architecture change → regenerate the graph
  (`update-context` skill runs `ckeel sync`).
- New/changed API → `Vault/Context/API Contracts.md`.
- Decision → an ADR in `Vault/Decisions/`.
- New term → `Vault/Context/Domain Glossary.md`.
- Finished a feature → prepend a 1-3 sentence entry to `Vault/Changelog.md`
  (newest first, plain language) so a returning user sees what shipped.

## Never
- Commit secrets. Overwrite a file without need. Trust code over context without
  reconciling the two.
