---
name: lang-typescript
description: TypeScript/JavaScript idioms (defers to Vault/Context/Conventions.md)
globs: **/*.{ts,tsx,js,jsx,mjs,cjs}
always_apply: false
---
# TypeScript / JavaScript

Follow `Vault/Context/Conventions.md` first. Language idioms:

- Prefer TypeScript with `strict` mode; avoid `any` — use `unknown` + narrowing.
- `const` by default; no `var`. Use `async/await`, not raw `.then()` chains.
- Named exports over default exports for discoverability.
- Validate external input at boundaries (e.g. zod) before trusting it.
- Errors: throw `Error` subclasses; never `throw` strings.
- Use the project's package manager from `project.yml` (`pnpm`/`npm`/`yarn`/`bun`).
- Tests with the configured runner (`vitest`/`jest`); colocate `*.test.ts`.
- Format with Prettier, lint with ESLint when configured.
