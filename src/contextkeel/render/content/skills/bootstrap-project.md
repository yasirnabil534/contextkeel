---
name: bootstrap-project
description: Initialize an empty repository into a runnable project (frontend, backend, or full-stack) based on project.yml — set up the tiers, directory structure, tooling, and the initial context notes. Use when starting a greenfield project or when there is no source code yet.
model_invocable: true
---
# Bootstrap Project

Turn `project.yml` (plus defaults) into a working skeleton for the declared tiers.

## Steps
1. Read `project.yml`; resolve `auto`/empty fields from `defaults:`. Note
   `project.type` and whether it's a monorepo. Briefly confirm the resolved stack
   before generating files.
2. If full-stack / monorepo, lay out workspaces (e.g. `apps/web` + `apps/api`, or
   `pnpm-workspace.yaml` / `turbo.json`) before initializing each tier.
3. **Frontend tier** (if any): scaffold by `frontend.platform`/`framework`:
   - **web** → `npm create vite@latest`, `npx create-next-app`,
     `npm create vue@latest`, `npx sv create` (SvelteKit), `ng new`.
   - **mobile** → `npx create-expo-app` (Expo) or `npx @react-native-community/cli init`.
   - **desktop** → `npm create @quick-start/electron` / Electron Forge, or
     `npm create tauri-app`.
   Add styling (Tailwind/NativeWind) and state if configured.
4. **Backend tier** (if any): init with the language's tool —
   Node `npm init`/`pnpm init` (+ tsconfig), Python `uv init`/`poetry new`,
   .NET `dotnet new`, Rust `cargo init`, Go `go mod init`. Add a minimal runnable
   entry point and DB/ORM wiring if configured.
5. Configure shared tooling: formatter, linter, unit test framework, e2e
   framework, and a CI file if `conventions.ci` is set.
6. Install dependencies for each tier.
7. Seed the context store: fill `Vault/Context/Tech Stack.md`, sketch
   `Architecture.md` (pattern/rationale only), and build the initial graph
   (`ckeel sync --full`) so structure is queryable from the start.
8. Verify each tier builds and its test command runs (even one stub test).

## Rules
- Substitute real values into template tokens (no literal `{{...}}`).
- Don't add frameworks/libraries beyond what `project.yml` implies without asking.
