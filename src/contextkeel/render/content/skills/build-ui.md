---
name: build-ui
description: Build UI according to project.yml ui.mode — generate it from conventions (agent), implement it from a Figma source (figma), or skip it (none). Use when asked to build, design, or implement UI/frontend.
model_invocable: true
---
# Build UI

Branch on `ui.mode` in `project.yml`.

## mode: none
Do not build UI. If the user asks for UI anyway, confirm they want to change
`ui.mode` first.

## mode: agent
1. Read `frontend.platform`, `frontend.framework`, `styling`/`state` (or detect).
2. Build for the platform (idioms in the `frontend` rule):
   - **web** → accessible, responsive components; project styling approach.
   - **mobile** (React Native/Expo) → RN primitives (`View`/`Text`), `StyleSheet`/
     NativeWind, safe areas, `react-navigation`/`expo-router`. No DOM elements.
   - **desktop** (Electron/Tauri) → web UI in the renderer, but route native/OS
     access through a preload bridge with `contextIsolation`; never expose
     Node/OS APIs to the renderer directly.
3. Reuse existing components and design tokens; keep styles colocated.
4. Wire to the API per `Vault/Context/API Contracts.md`.

## mode: figma
1. Read `ui.figma` (URL or local path) for the design source.
2. Use the Figma MCP / Code Connect tooling when available to translate the
   design faithfully (spacing, tokens, components). See the Figma skills.
3. Map Figma components to existing code components where they exist; create new
   ones only when needed.
4. Match the design's tokens rather than hardcoding values.

## After
Run `update-context` to regenerate the graph with the new UI modules.
