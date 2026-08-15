---
name: write-commit
description: Generate a commit message from staged changes following the project's commit style (Conventional Commits by default). Use when asked to commit, write a commit message, or describe staged changes.
model_invocable: true
---
# Write Commit

## Steps
1. Inspect staged changes: `git diff --cached --stat` then `git diff --cached`.
2. Read `conventions.commit_style` in `project.yml` (default: `conventional`).
3. Compose the message:
   - **conventional**: `type(scope): summary` where type ∈ `feat|fix|refactor|
     docs|test|chore|perf|build|ci`. Summary in imperative mood, ≤ 72 chars.
   - Add a body explaining **why** when the change isn't trivial.
   - **plain**: a concise imperative summary + optional body.
4. One logical change per commit. If staged changes span unrelated concerns,
   suggest splitting them.

## Safety
- Never include secrets or large generated blobs in the message.
- Only run `git commit` when the user asks you to; otherwise just propose the message.

## Example
```
feat(auth): add refresh-token rotation

Rotate refresh tokens on each use and revoke the previous one to limit
replay risk. Adds a token_version column and middleware check.
```
