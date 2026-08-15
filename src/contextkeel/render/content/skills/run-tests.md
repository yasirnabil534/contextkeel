---
name: run-tests
description: Run the project's tests (unit, component, and e2e) using the correct command for its stack, inferred from project.yml and manifests. Use when asked to run, fix, or add tests for frontend, backend, or full-stack.
model_invocable: true
---
# Run Tests

Pick the right command(s) for the detected tiers.

## Unit / backend
From `project.yml` `conventions.test_framework` (or detect):

| Stack | Command |
|-------|---------|
| Node + vitest | `pnpm vitest run` / `npm run test` |
| Node + jest | `npm test` / `pnpm jest` |
| Python + pytest | `pytest` (or `uv run pytest` / `poetry run pytest`) |
| .NET | `dotnet test` |
| Rust | `cargo test` |
| Go | `go test ./...` |

## Frontend component
- React/Vue/Svelte + vitest/jest + Testing Library → the project's `test` script.
- Run a specific component test by path when iterating.

## End-to-end
From `conventions.e2e_framework`:
- Playwright → `npx playwright test`
- Cypress → `npx cypress run`

## Steps
1. Detect tiers and package manager (lockfiles tell you which).
2. Run the relevant suite(s); in a monorepo, scope to the affected workspace.
3. On failure: read the error, fix the root cause (code or test), re-run until
   green. Don't weaken assertions to force a pass.
4. For new behavior, add a test named after the behavior (unit for logic,
   component for UI, e2e for user flows).
