---
name: frontend
description: Frontend / client UI idioms for web, mobile, and desktop (defers to Vault/Context/Conventions.md)
globs: **/*.{tsx,jsx,vue,svelte}
always_apply: false
---
# Frontend / Client UI

Follow `Vault/Context/Conventions.md` first. Check `frontend.platform` and
`frontend.framework` in `project.yml` — the same `.tsx` file can be web, mobile
(React Native), or desktop (Electron/Tauri), so the platform decides the idioms.

## All platforms
- Small, focused, reusable components; lift state only as far as needed.
- Reuse existing components/design tokens before creating new ones.
- Keep data-fetching/logic out of presentational components (hooks/containers/
  composables/stores per the framework).
- Type API responses; call endpoints per `Vault/Context/API Contracts.md`.
- Handle loading, empty, and error states explicitly. No stray console logs.
- Use the project's state solution (`frontend.state`); don't add one ad hoc.

## platform: web
- Semantic HTML, labelled inputs, keyboard navigable, visible focus.
- Responsive by default; respect `prefers-reduced-motion`.
- Use the project's styling approach (`frontend.styling`, e.g. Tailwind / CSS
  modules); don't mix paradigms. Colocate styles with components.

## platform: mobile (React Native / Expo)
- Use RN primitives (`View`, `Text`, `Pressable`) — there is no DOM, no `div`.
- Style via `StyleSheet`/NativeWind; respect safe-area insets and platform
  differences (`Platform.select`). Navigation via `frontend.navigation`.
- Mind list performance (`FlatList`/`FlashList`), touch targets, and offline.

## platform: desktop (Electron / Tauri)
- Keep a strict main/renderer (or core/webview) boundary; never expose Node/OS
  APIs straight to the renderer — use a preload bridge / `contextIsolation`.
- Treat the renderer like a web app for UI idioms.
- Gate filesystem/shell/native calls; validate anything crossing the boundary.

## Tests
- Component tests with Testing Library (or RN Testing Library); e2e for user
  flows (`conventions.e2e_framework`; Detox/Maestro for mobile).
