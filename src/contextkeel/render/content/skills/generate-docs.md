---
name: generate-docs
description: Keep documentation in sync with code — refresh API Contracts, README usage, and code-level docs/docstrings. Use when endpoints, public APIs, or setup steps change, or when asked to update docs.
model_invocable: true
---
# Generate / Update Docs

## Steps
1. Determine what changed (recent diff or the area the user names).
2. Update the right surface:
   - Endpoints changed → `Vault/Context/API Contracts.md` (method, path, request,
     response, auth).
   - Public functions/modules → code-level docs (JSDoc, docstrings, XML docs,
     rustdoc) per the language's convention.
   - Setup/run steps changed → project `README.md`.
   - New module needing prose explanation beyond the graph → a
     `Vault/Templates/Module Note.md` note; then run `update-context` to
     regenerate the graph.
3. Keep docs DRY: describe and link, don't duplicate code into prose.

## Rules
- Documentation must match reality; if code and docs disagree, fix the docs (or
  flag the code) rather than leaving both.
- Don't generate docs for trivial, self-explanatory code.
