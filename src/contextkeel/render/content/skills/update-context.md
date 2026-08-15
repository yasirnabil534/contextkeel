---
name: update-context
description: Refresh the project context store after changes so it stays an accurate, token-saving memory — regenerates the code index, updates Vault/Context's prescriptive notes (Tech Stack, API Contracts, Domain Glossary) and ADRs, and logs a plain-language Changelog entry for the user. Use after adding modules, changing architecture, or finishing a feature.
model_invocable: false
---
# Update Context

Keep both halves of the context system truthful. Stale context is worse than
none.

## Steps
1. **Regenerate the graph (code structure — never hand-edit this):**
   - If `.contextkeel/index/index.json` doesn't exist yet: `ckeel sync --full` (full build).
   - Otherwise: `ckeel sync` (incremental — re-extracts only new/
     changed files, no LLM needed). Use `the code index . --update --force` only
     after a refactor that deleted a lot of code (data-loss guard otherwise
     refuses to shrink the graph).
   - Confirm the summary line (nodes/edges/communities) looks sane for the
     size of the change; if it doesn't, say so instead of assuming success.
2. **Update the Vault's prescriptive notes** — only what actually changed:
   - New/changed endpoint → `Vault/Context/API Contracts.md`.
   - Resolved stack detail → `Vault/Context/Tech Stack.md` (and `project.yml`).
   - New domain term → `Vault/Context/Domain Glossary.md`.
   - Architecture *pattern or rationale* changed (not just structure, which
     the graph already covers) → `Vault/Context/Architecture.md`.
3. If a significant choice was made, create an ADR (use `record-decision`).
4. **If a feature, module, or otherwise meaningful chunk of work just
   finished**, prepend a `Vault/Changelog.md` entry (newest first):
   `## YYYY-MM-DD — Title` + 1-3 plain-language sentences. This is written
   for the human returning to the project, not for other agents — no file
   lists, no diffs, no jargon. Don't add an entry for every small edit; one
   per unit of shipped work.
5. Keep notes short; prune anything no longer true. Don't duplicate what the
   graph already shows — describe intent/rules, not structure.

## Quality bar
- `.contextkeel/index/` reflects the current tree (run `--update`, don't skip it).
- `Tech Stack.md` matches `project.yml`.
- Don't duplicate code into notes — describe and link, don't paste.
- Changelog entries are readable by someone who wasn't in this session.
