---
name: load-context
description: Load the project's context store before doing work — reads project.yml, queries the code index for code structure, and reads Vault/Context for prescriptive rules, without scanning the whole codebase. Use at the start of a task or when context is unclear.
model_invocable: false
---
# Load Context

Build a working understanding cheaply, before touching source files. The
context system is hybrid: **the code index** for anything derived from the actual
code, **Vault** for anything prescriptive/human.

## Steps
1. Read `project.yml`. Note `project.type` (frontend/backend/fullstack) and read
   the tier blocks that apply, plus architecture, UI mode, and conventions.
2. For any `auto`/empty field, detect from manifests (`package.json`,
   `pyproject.toml`, `*.csproj`, `Cargo.toml`, `go.mod`, lockfiles). Fall back to
   the `defaults:` block.
3. **Code structure → the code index:**
   - If `the code index` isn't installed, run the `ckeel doctor --fix` skill first.
   - If `.contextkeel/index/index.json` doesn't exist yet, build it: `ckeel sync --full`
     (full pipeline; AST-only, no LLM/API key required for code).
   - If it exists, read `.contextkeel/index/REPORT.md` for the architecture
     overview and communities. For a specific question ("how does X work?",
     "what calls Y?"), don't hand-roll a search — use the **the code index skill**
     installed by `ckeel doctor --fix` (`the code index install --platform claude`
     already dropped it into this repo's skills); it knows the query/`explain`/
     `path` workflow against `.contextkeel/index/index.json` far better than a
     from-scratch grep would.
   - If the graph looks stale for the change at hand (new files not reflected),
     tell the user and offer to run `update-context` to refresh it.
4. **Prescriptive rules → Vault:** read `Vault/Context/Conventions.md`, and
   skim `Domain Glossary.md` + `API Contracts.md` + `Tech Stack.md`.
5. Use what the graph told you to locate relevant code; open only those files.

## Output
Briefly summarize: resolved stack, the 1-3 modules relevant to the task (from
the graph), and any context gaps you noticed.
