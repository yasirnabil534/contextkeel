---
name: write-prompt-plan
description: Break down requirements for a new project, module, or large feature into phased, dependency-tracked AI-prompt lists split by tier (frontend/backend/mobile), written to a .docs folder with a migration-style registry so multiple developers can track progress without colliding. Use before writing any code whenever the user hands over requirements for a new project or a large feature.
model_invocable: true
---
# Write Prompt Plan

Turn requirements into an executable, trackable plan **before** touching code.
Planning and execution are separate steps — generate the plan, then only start
implementing prompts when the user asks you to.

## Steps

1. **Load context.** Run `load-context` (read `project.yml` + `Vault/Context/`)
   to know the resolved stack, architecture, and existing modules. If this is a
   rewrite/migration of an existing codebase (like porting Django → FastAPI),
   identify the source project's location too — prompts will tell the AI to
   read from it.

2. **Decide which files to create**, based on `project.yml` tiers:
   - `.docs/frontend_prompt_list.md` — if a web frontend tier applies
   - `.docs/backend_prompt_list.md` — if a backend tier applies
   - `.docs/mobile_prompt_list.md` — if `frontend.platform: mobile`
   - Desktop apps reuse `frontend_prompt_list.md` unless the user wants it split
     out separately.
   Create only the files for tiers that actually apply. Create `.docs/` at the
   target project's root if it doesn't exist.

3. **Read `template.md`** in this skill's folder — it is the exact document
   skeleton to fill in (header block, migration registry table, boxed prompt
   blocks). Follow it precisely; don't invent a different format.

4. **Break the requirements into scopes and prompts:**
   - Group work into scopes (`S0`, `S1`, `S2`, …): `S0` is manual environment
     setup (never run via AI); later scopes are logical groups (core
     infrastructure, then one scope per feature/vertical slice, then tests,
     then deployment).
   - Each prompt targets **one file or one tight cluster of files** — small
     enough for a junior developer or an AI agent to execute in one shot and
     verify immediately.
   - Assign sequential codes per tier prefix: `FE-0001`, `BE-0001`, `MOB-0001`
     (pick a short, obvious prefix from the project name if the user has one,
     e.g. `GMS-0001`). Zero-pad to 4 digits.
   - For every prompt, fill in: DEPENDS ON (prior codes it needs), NEXT (the
     following code), FILES (exact paths), and a VERIFY step (a command or
     manual check proving it worked) wherever one is meaningful.
   - Encode this project's actual conventions into the "CODING RULES" header
     block by pulling from `Vault/Context/Conventions.md` and the matching
     `the language rules` — don't leave generic placeholder rules.

5. **Write the migration registry table first**, then the individual prompt
   blocks in the same order. Every code in the registry must have a matching
   block below, and vice versa.

6. **Set every prompt's STATUS to `[ ] PENDING`** initially (unless the user
   states some parts are already built — verify before marking `[x] DONE`).

## Tracking conventions (multiple people, migration-style)

- The registry table is the shared source of truth — treat it like a
  migrations table. Whoever picks up work claims the **lowest `[ ] PENDING`**
  code in their assigned scope, marks it `[~] IN PROGRESS (initials)`, and
  commits that single-line change immediately so others don't duplicate it.
- On completion, flip to `[x] DONE` (add a short note if there was a deviation
  from the original plan) and commit again. Never skip a pending code.
- **Inserting a prompt later** (a retrofit / missed requirement): give it the
  previous code's number + a letter suffix (e.g. `BE-0009A`), insert its block
  physically after that code, and update the neighboring prompts' `DEPENDS ON`
  / `NEXT` pointers — exactly like a manually-inserted DB migration.
- To check overall progress across tiers, search all three files for
  `[ ] PENDING` / `[x] DONE`.

## After generating the plan

Tell the user which `.docs/*.md` files were created, how many scopes/prompts
each contains, and wait for them to say "execute" or name a specific prompt
before writing implementation code. When executing a prompt, use
`scaffold-feature` or `bootstrap-project` as the underlying implementation
skill, then flip that prompt's status and run `update-context`.

## Additional resources

- Document skeleton to fill in: [template.md](template.md)
