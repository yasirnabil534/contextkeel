---
name: scaffold-feature
description: Scaffold a new feature in a stack-aware way across frontend, backend, or full-stack, by reading project.yml and the context store, then generating code that fits the project's frameworks, architecture, and conventions. Use when asked to add a feature, page, endpoint, component, or module.
model_invocable: true
---
# Scaffold Feature

Generate new code that matches THIS project, for whichever tiers apply.

## Steps
1. Run `load-context` (read `project.yml` + `Vault/Context/`). Note `project.type`.
2. Resolve the relevant tiers:
   - Frontend → framework, build tool, styling, state.
   - Backend → language, framework, db/orm, api style.
   - Architecture pattern(s) and test frameworks.
3. For non-trivial work, draft a short spec from `Vault/Templates/Feature Spec.md`
   and confirm scope/acceptance criteria.
4. Implement per tier, placing files by the architecture pattern
   (`Vault/Context/Architecture.md`) and the existing structure
   (`.contextkeel/index/REPORT.md`):
   - **Backend**: layered → controller/service/repository; clean/hexagonal →
     domain core + ports/adapters; mvc → models/views/controllers. Add the
     endpoint/handler, validation, and data access via the ORM/driver.
   - **Frontend**: follow the project's structure (feature-folders / atomic /
     container-presentational). Add components/pages/routes, hook them to state,
     and call the API per `Vault/Context/API Contracts.md`.
5. **Full-stack**: implement the API and the UI that consumes it together, keep
   the request/response types shared or mirrored, and update `API Contracts.md`.
6. If UI is required and `ui.mode` is `agent`/`figma`, use the `build-ui` skill.
7. Add tests (unit for logic, component for UI, and an e2e if it's a user flow).
8. Run `update-context` to record new modules/endpoints/components.

## Rules
- Reuse existing utilities, components, and patterns; don't fork the style.
- Don't introduce a new framework/library without asking (`add-dependency`).
