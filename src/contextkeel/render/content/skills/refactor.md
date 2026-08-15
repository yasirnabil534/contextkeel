---
name: refactor
description: Perform safe, behavior-preserving refactors that follow the project's conventions, verifying with tests at each step. Use when asked to clean up, restructure, rename, or improve code without changing behavior.
model_invocable: true
---
# Refactor

Change structure, not behavior.

## Steps
1. Ensure a safety net: confirm relevant tests exist and pass first. If coverage
   is thin, add characterization tests before refactoring.
2. Make small, behavior-preserving steps (rename, extract, inline, move).
3. Re-run tests (`run-tests`) after each meaningful step; keep them green.
4. Follow `Vault/Context/Conventions.md` and the matching `lang-*` idioms.
5. Regenerate the graph (`ckeel sync`) and fix imports if files or
   modules moved.

## Rules
- **Never** mix a refactor with a behavior change in the same commit.
- Stop and ask if a "refactor" would alter public APIs or observable behavior.
- Prefer mechanical, reversible transforms over sweeping rewrites.
