---
name: review-changes
description: Review code changes against this project's conventions, architecture, security, and test coverage, producing severity-grouped feedback. Use when asked to review a diff, a PR, staged changes, or before merging.
model_invocable: true
---
# Review Changes

Review against THIS project's standards, not generic taste.

## Steps
1. Get the diff: staged (`git diff --cached`), branch (`git diff main...HEAD`), or
   the files the user names.
2. Load context (`load-context`) so you know the conventions and architecture.
3. Check each change for:
   - Correctness and edge cases.
   - Consistency with `Vault/Context/Conventions.md` and the matching `lang-*` rule.
   - Fit with the architecture pattern (`Architecture.md`) and existing
     structure (`.contextkeel/index/REPORT.md`) — right layer/module.
   - Security: injection, authz gaps, secrets, unsafe input handling.
   - Tests cover the change.
   - Context store updated if modules/APIs/decisions changed.

## Output
Group by severity with specific `file:line` references and a proposed fix:
- 🔴 Critical — must fix before merge
- 🟡 Suggestion — should consider
- 🟢 Nice-to-have — optional
