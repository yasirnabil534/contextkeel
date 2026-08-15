---
name: add-dependency
description: Add a third-party dependency the right way for the project's package manager, justifying the need and updating the context store. Use when asked to add, install, or introduce a library/package.
model_invocable: true
---
# Add Dependency

## Steps
1. Resolve the package manager from `project.yml` (or lockfiles).
2. Justify it first: is there already a dependency or stdlib feature that covers
   this? Avoid redundant or unmaintained packages; prefer well-supported ones.
3. Add with the correct command:
   - npm/pnpm/yarn/bun → `pnpm add <pkg>` (`-D` for dev)
   - pip/poetry/uv → `uv add <pkg>` / `poetry add <pkg>`
   - .NET → `dotnet add package <pkg>`
   - Rust → `cargo add <pkg>`
   - Go → `go get <pkg>`
4. Pin sensibly and commit the lockfile change.
5. If it's a significant dependency (framework, db driver, auth), note it in
   `Vault/Context/Tech Stack.md` and consider an ADR via `record-decision`.

## Rules
- Never add a dependency to work around a small, easily-written helper.
- Check license compatibility for anything non-trivial.
