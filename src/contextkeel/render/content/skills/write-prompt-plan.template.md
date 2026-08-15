# Prompt List Template

Fill this skeleton in for each `.docs/<tier>_prompt_list.md` file. Replace every
`{PLACEHOLDER}`. Keep the box-drawing formatting — it is scanned visually by
humans copying prompt blocks into a chat, so alignment matters. Everything
below the "START OF FILE" marker is the literal document to produce.

---

START OF FILE

```
# {PROJECT_NAME} — {TIER_LABEL}
# AI Prompt List for Junior Developers / Agents
# Architecture: {ARCHITECTURE_PATTERN}
# ─────────────────────────────────────────────────────────────────────────────
# IDE SETUP (do this once before running any prompt):
# 1. Open {SETUP_SCOPE} in Cursor / Claude Code / Continue / VS Code + Copilot.
#    {SETUP_NOTES — e.g. "gives the AI access to both the old and new project
#    at once" for a migration, or just the repo root for a greenfield build.}
#
# RUNNING A PROMPT:
# 2. Find the LOWEST prompt with STATUS: [ ] PENDING in the registry below
#    (within your assigned scope, if working alongside others).
# 3. Mark it [~] IN PROGRESS (your initials) and commit that one-line change.
# 4. Copy that prompt's full block — paste it into your AI chat exactly as written.
# 5. Review the output, run the VERIFY command, fix any errors.
# 6. Mark the prompt [x] DONE in the registry table (note any deviation) and commit.
# 7. Move to the next PENDING prompt. Never skip one.
#
# CONCURRENCY (multiple people): this registry is the shared source of truth —
#   treat it like a migrations table. Claim only the lowest PENDING code in
#   your scope. Commit registry edits immediately so others see them.
#   To insert a missed/retrofit prompt later, suffix the previous code with a
#   letter (e.g. {PREFIX}-0009A), insert its block after that code, and fix the
#   neighboring DEPENDS ON / NEXT pointers.
#
# CODING RULES (enforce in every prompt — pulled from Vault/Context/Conventions.md):
# - {RULE_1}
# - {RULE_2}
# - {RULE_3 — add the language-specific must-haves from the matching lang-*.mdc}
# ─────────────────────────────────────────────────────────────────────────────


# ═════════════════════════════════════════════════════════════════════════════
# MIGRATION REGISTRY  —  mark each prompt [x] DONE after successful execution
# ═════════════════════════════════════════════════════════════════════════════
#
#  CODE          │ SCOPE │ TITLE                                    │ STATUS
# ───────────────┼───────┼──────────────────────────────────────────┼──────────
#  {PREFIX}-0000 │  S0   │ {Manual environment setup title}         │ [ ] PENDING
#  {PREFIX}-0001 │  S1   │ {First core-infra file}                  │ [ ] PENDING
#  {PREFIX}-0002 │  S1   │ {...}                                    │ [ ] PENDING
#  ...           │  S2   │ {Feature slice N, one row per file}      │ [ ] PENDING
# ───────────────┼───────┼──────────────────────────────────────────┼──────────
# (list every code; keep this table and the boxed blocks below in the same order)


════════════════════════════════════════════════════════════════════════════════
SCOPE 0 — ENVIRONMENT SETUP (manual — run in terminal, NOT via AI)
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : {PREFIX}-0000                                                 │
│  SCOPE      : S0 — Environment Setup                                       │
│  TITLE      : {short title}                                                │
│  DEPENDS ON : —                                                            │
│  NEXT       : {PREFIX}-0001                                                │
│  STATUS     : [ ] PENDING                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

Run these commands manually (do NOT paste into the AI):

```bash
{setup commands — init repo, create folder skeleton, venv/toolchain, etc.}
```

[VERIFY] {a command confirming the setup worked}


════════════════════════════════════════════════════════════════════════════════
SCOPE 1 — {SCOPE_1_NAME}
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : {PREFIX}-0001                                                 │
│  SCOPE      : S1 — {SCOPE_1_NAME}                                          │
│  TITLE      : {file or feature being created}                              │
│  DEPENDS ON : {PREFIX}-0000                                                 │
│  NEXT       : {PREFIX}-0002                                                │
│  FILES      : {exact file path(s) this prompt creates}                     │
│  STATUS     : [ ] PENDING                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

{If this is a migration/rewrite: "Read `{SOURCE_PATH}` — look at ... . Then
create `{TARGET_PATH}`." If greenfield: describe the requirement directly.}

{Precise, unambiguous instructions for exactly what to build in this ONE file
or tight cluster of files — fields, function signatures, endpoints, whatever
is concrete enough that two different developers would produce equivalent
output. Reference `Vault/Context/Architecture.md` (pattern) and
`.contextkeel/index/REPORT.md` (current structure) for where this fits and
what it must be consistent with.}

[VERIFY] {command or manual check}

<!-- Repeat one boxed block per prompt, grouped under "SCOPE N — ..." headers,
     in the same order as the registry table above. Insert a real ★ marker on
     titles for exceptionally complex or critical prompts, matching the
     registry's visual cue, so nobody underestimates them. -->

END OF FILE
```
