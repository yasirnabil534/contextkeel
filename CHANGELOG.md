# Changelog

Releases of the **contextkeel package**. Not to be confused with the
`Vault/Changelog.md` that contextkeel generates inside *your* project — that
one records what shipped in your work, in plain language, for you.

Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [0.1.0] — 2026-08-16

### Added
- One-line installers for macOS/Linux (`install.sh`) and Windows
  (`install.ps1`) that need nothing pre-installed: uv is bootstrapped first and
  supplies its own Python, so no system package manager and no sudo is
  involved on the normal path.
- `ckeel init` — detects the stack, writes editor configs, scaffolds notes,
  installs hooks, and builds a code index in one command.
- `ckeel doctor` / `doctor --fix`, `ckeel sync`, `ckeel status`, `ckeel plan`.
- Pluggable index backends: graphify when available, otherwise a bundled
  tree-sitter indexer that works offline. Degradation is silent and the output
  is identical either way.
- `ckeel internals` and `--expert` — full disclosure of every underlying tool,
  command and override for anyone who wants it.
- MCP server exposing `load_context`, `query_index`, `sync_context`, `status`
  and `plan`, registered automatically for every supported editor.
- Claude Code, Cursor and Continue configs generated from one canonical source,
  so they cannot drift apart.
