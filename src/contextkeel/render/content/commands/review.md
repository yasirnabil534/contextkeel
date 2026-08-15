---
name: review
description: Review changes against project conventions and architecture
---
Run the `review-changes` skill: review the diff (staged, branch vs main, or named
files) against the project's conventions, architecture, security, and test
coverage. Return feedback grouped as 🔴 critical / 🟡 suggestion / 🟢 nice-to-have
with file:line references.

Scope: $ARGUMENTS
