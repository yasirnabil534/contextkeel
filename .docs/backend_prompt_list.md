# contextkeel — Package / CLI Tier (single tier: no UI)
# AI Prompt List for Junior Developers / Agents
# Architecture: layered Python package (bootstrap -> core -> backends -> renderers -> surfaces)
# ─────────────────────────────────────────────────────────────────────────────
# WHAT THIS PROJECT IS:
#   A cross-platform Python package that turns any repo into a self-maintaining
#   agent context workspace. The developer runs ONE line, ever, and from then on
#   never thinks about context, indexing, or project memory again.
#
#   THE PRODUCT PROMISE — it constrains almost every prompt below:
#   the developer never learns the name of any internal tool, never installs
#   anything by hand, and is never blocked by missing configuration.
#
# IDE SETUP (do this once before running any prompt):
# 1. Open the contextkeel repo root in Cursor / Claude Code / Continue.
#    Keep this template repo open alongside it — several prompts port content
#    out of it (its .cursor/, .claude/, .continue/, and Vault/ trees are the
#    source material for CK-0019 and CK-0024).
#
# RUNNING A PROMPT:
# 2. Find the LOWEST prompt with STATUS: [ ] PENDING in the registry below
#    (within your assigned scope, if working alongside others).
# 3. Mark it [~] IN PROGRESS (your initials) and commit that one-line change.
# 4. Copy that prompt's full block — paste it into your AI chat exactly as written.
# 5. Review the output, run the VERIFY command, fix any errors.
# 6. Mark the prompt [x] DONE in the registry table (note any deviation) and commit.
# 7. Move to the next PENDING prompt. Never skip one.
#
# CONCURRENCY (multiple people): this registry is the shared source of truth —
#   treat it like a migrations table. Claim only the lowest PENDING code in
#   your scope. Commit registry edits immediately so others see them.
#   To insert a missed/retrofit prompt later, suffix the previous code with a
#   letter (e.g. CK-0009A), insert its block after that code, and fix the
#   neighbouring DEPENDS ON / NEXT pointers.
#
# PARALLEL WORK: after S1 is complete, S3 / S4 / S5 are independent of each
#   other and can be worked by three people at once. S7 needs S3+S4+S5.
#
# CODING RULES (enforce in every prompt — from Vault/Context/Conventions.md
#               and .cursor/rules/lang-python.mdc):
# - Target Python 3.11+. Full type hints on every public function.
# - PEP 8: snake_case functions/vars, PascalCase classes. Ruff-clean.
# - Prefer pathlib over os.path; f-strings over % / .format.
# - Pydantic v2 or dataclasses for structured data; validate external input.
# - Raise specific exceptions; never bare `except:`; never swallow errors
#   silently — EXCEPT in hook code (CK-0032), which must fail open by design.
# - Keep side effects out of import time; guard scripts with __main__.
# - No secrets in code or config; environment variables only.
# - Every behaviour change ships with a pytest test named after the behaviour.
# - Keep changes small and focused; match the style of the file you edit.
# - Conventional Commits; one logical change per commit.
#
# PROJECT-SPECIFIC RULES (violating either of these is a release blocker):
# - VOCABULARY (progressive disclosure, NOT a ban): the DEFAULT register uses
#   neutral terms ("code index", "notes viewer") so a developer never has to
#   learn an internal tool's name to use this product. The EXPERT register
#   (--expert, --verbose, --json, or CONTEXTKEEL_EXPERT=1) names every tool,
#   prints the exact commands being run, and exposes every override.
#   Nothing is ever hidden from someone who asks for it, and nothing is ever
#   forbidden — only defaulted away. Enforced in BOTH directions by CK-0042:
#   default output must not leak names, expert output must reveal them.
# - CROSS-PLATFORM: macOS, Windows, and Linux are equal targets. All OS
#   branching lives in platform.py. All subprocess calls go through
#   platform.run(). Never assume POSIX paths, shells, or encodings.
# ─────────────────────────────────────────────────────────────────────────────


# ═════════════════════════════════════════════════════════════════════════════
# MIGRATION REGISTRY  —  mark each prompt [x] DONE after successful execution
# ═════════════════════════════════════════════════════════════════════════════
#
#  CODE     │ SCOPE │ TITLE                                                    │ STATUS
# ──────────┼───────┼──────────────────────────────────────────────────────────┼──────────
#  CK-0000  │  S0   │ Repo, toolchain, and package skeleton                    │ [x] DONE
# ──────────┼───────┼──────────────────────────────────────────────────────────┼──────────
#  CK-0001  │  S1   │ ★ pyproject.toml — packaging, deps, and both CLI entr... │ [x] DONE
#  CK-0002  │  S1   │ Package init and single-sourced version                  │ [x] DONE
#  CK-0003  │  S1   │ Exception hierarchy with user-safe messages              │ [x] DONE
#  CK-0004  │  S1   │ ★ Cross-platform primitives                              │ [x] DONE
#  CK-0005  │  S1   │ Console output and the vocabulary guard                  │ [x] DONE
#  CK-0006  │  S1   │ ★ project.yml model, auto-detection, and defaults        │ [x] DONE
#  CK-0007  │  S1   │ Workspace discovery and path layout                      │ [x] DONE
#  CK-0008  │  S1   │ Durable state file                                       │ [x] DONE
# ──────────┼───────┼──────────────────────────────────────────────────────────┼──────────
#  CK-0009  │  S2   │ ★ POSIX bootstrap installer                              │ [x] DONE
#  CK-0010  │  S2   │ ★ Windows bootstrap installer                            │ [x] DONE
#  CK-0011  │  S2   │ Programmatic toolchain repair                            │ [x] DONE
#  CK-0012  │  S2   │ Self-upgrade and state migration                         │ [x] DONE
# ──────────┼───────┼──────────────────────────────────────────────────────────┼──────────
#  CK-0013  │  S3   │ ★ Backend-neutral index interface                        │ [x] DONE
#  CK-0014  │  S3   │ Default backend adapter                                  │ [x] DONE
#  CK-0015  │  S3   │ ★ Bundled offline fallback indexer                       │ [x] DONE
#  CK-0016  │  S3   │ ★ Backend selection and silent degradation               │ [x] DONE
#  CK-0017  │  S3   │ Index report rendering                                   │ [x] DONE
# ──────────┼───────┼──────────────────────────────────────────────────────────┼──────────
#  CK-0018  │  S4   │ Vault scaffolding                                        │ [x] DONE
#  CK-0019  │  S4   │ Bundled vault templates with real substitution           │ [x] DONE
#  CK-0020  │  S4   │ Section-level note updates                               │ [x] DONE
#  CK-0021  │  S4   │ Changelog entries and ADR allocation                     │ [x] DONE
#  CK-0022  │  S4   │ Optional viewer — best-effort and silent                 │ [x] DONE
# ──────────┼───────┼──────────────────────────────────────────────────────────┼──────────
#  CK-0023  │  S5   │ ★ Canonical agent-config model                           │ [x] DONE
#  CK-0024  │  S5   │ ★ The single canonical content source                    │ [x] DONE
#  CK-0025  │  S5   │ Claude Code target renderer                              │ [x] DONE
#  CK-0026  │  S5   │ Cursor target renderer                                   │ [x] DONE
#  CK-0027  │  S5   │ Continue target renderer                                 │ [x] DONE
#  CK-0028  │  S5   │ ★ MCP config generation with resolved paths              │ [x] DONE
#  CK-0029  │  S5   │ ★ Render orchestration, atomic writes, drift detection   │ [x] DONE
# ──────────┼───────┼──────────────────────────────────────────────────────────┼──────────
#  CK-0030  │  S6   │ Hook payload definitions                                 │ [x] DONE
#  CK-0031  │  S6   │ Hook installation via the render engine                  │ [x] DONE
#  CK-0032  │  S6   │ ★ Hidden hook runner — fails open, always                │ [x] DONE
# ──────────┼───────┼──────────────────────────────────────────────────────────┼──────────
#  CK-0033  │  S7   │ CLI application shell                                    │ [x] DONE
#  CK-0034  │  S7   │ ★ `ckeel init` — the whole product in one command        │ [x] DONE
#  CK-0035  │  S7   │ ★ `ckeel doctor` — verify and self-repair                │ [x] DONE
#  CK-0036  │  S7   │ `ckeel sync` — keep context true                         │ [x] DONE
#  CK-0037  │  S7   │ ★ `ckeel plan` — prompt-plan generation as a command     │ [x] DONE
#  CK-0038  │  S7   │ `ckeel status` — the human summary                       │ [x] DONE
#  CK-0038A │  S7   │ ★ Expert mode and escape hatches                         │ [x] DONE
# ──────────┼───────┼──────────────────────────────────────────────────────────┼──────────
#  CK-0039  │  S8   │ ★ MCP server                                             │ [x] DONE
#  CK-0040  │  S8   │ MCP tool definitions                                     │ [x] DONE
# ──────────┼───────┼──────────────────────────────────────────────────────────┼──────────
#  CK-0041  │  S9   │ Test fixtures and harness                                │ [x] DONE
#  CK-0042  │  S9   │ ★ Golden render tests and the invariant assertions       │ [x] DONE
#  CK-0043  │  S9   │ ★ Degradation tests                                      │ [x] DONE
#  CK-0044  │  S9   │ ★ End-to-end CLI tests                                   │ [x] DONE
#  CK-0045  │  S9   │ ★ CI matrix                                              │ [x] DONE
#  CK-0046  │  S9   │ Release workflow                                         │ [x] DONE
# ──────────┼───────┼──────────────────────────────────────────────────────────┼──────────
#  CK-0047  │  S10  │ README                                                   │ [x] DONE
#  CK-0048  │  S10  │ CI drift-check template for user repos                   │ [x] DONE
#  CK-0049  │  S10  │ LICENSE, changelog, and release checklist                │ [x] DONE
# ──────────┴───────┴──────────────────────────────────────────────────────────┴──────────
# ★ = exceptionally critical or complex — do not underestimate these.
# 51 prompts across 11 scopes.

════════════════════════════════════════════════════════════════════════════════
SCOPE 0 — ENVIRONMENT SETUP (manual — run in terminal, NOT via AI)
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0000                                                       │
│  SCOPE      : S0 — Environment Setup                                        │
│  TITLE      : Repo, toolchain, and package skeleton                         │
│  DEPENDS ON : —                                                             │
│  NEXT       : CK-0001                                                       │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Run these commands manually (do NOT paste into the AI):

```bash
# 1. Create and enter the repo
mkdir contextkeel && cd contextkeel && git init

# 2. Ensure Python 3.11+ and uv exist on THIS machine (the package will later
#    do this for end users automatically — right now it's just for developing)
python3 --version        # need >= 3.11
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS/Linux
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 3. Directory skeleton
mkdir -p src/contextkeel/{bootstrap,graph,vault,render/targets,hooks,cli,mcp}
mkdir -p src/contextkeel/render/content src/contextkeel/vault/templates
mkdir -p bootstrap tests .github/workflows docs templates

# 4. Pin the interpreter and create the venv
uv python pin 3.11
uv venv
```

[VERIFY] `uv --version` prints a version and `ls src/contextkeel` shows the subpackages.

════════════════════════════════════════════════════════════════════════════════
SCOPE 1 — PACKAGE FOUNDATION
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0001                                                       │
│  SCOPE      : S1 — Package Foundation                                       │
│  TITLE      : ★ pyproject.toml — packaging, deps, and both CLI entry points │
│  DEPENDS ON : CK-0000                                                       │
│  NEXT       : CK-0002                                                       │
│  FILES      : pyproject.toml                                                │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Create the project's build configuration. This file decides how every end user
installs the tool, so get it right before anything else.

- Build backend: `hatchling`. `src/` layout, package `contextkeel`.
- `name = "contextkeel"`, `requires-python = ">=3.11"`, version single-sourced
  from `src/contextkeel/__about__.py` via hatch's version hook.
- Runtime dependencies: `typer`, `pydantic>=2`, `ruamel.yaml` (round-trips
  project.yml *with comments intact* — plain pyyaml would destroy them),
  `jinja2`, `platformdirs`, `mcp`.
- Optional extra `index` : `tree-sitter`, `tree-sitter-language-pack` — used by
  the bundled fallback indexer (CK-0015). Include it in the default install so
  the fallback always works offline.
- Two console scripts, both pointing at the same Typer app:
  `contextkeel = "contextkeel.cli.main:app"` and `ckeel = "contextkeel.cli.main:app"`.
- Include package data: `render/content/**`, `vault/templates/**`, `templates/**`.
- Configure `ruff` (line-length 88, target py311) and `pytest`
  (`testpaths = ["tests"]`, `--strict-markers`, a `network` marker).

[VERIFY] `uv build` produces a wheel and `uv run ckeel --help` exits 0.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0002                                                       │
│  SCOPE      : S1 — Package Foundation                                       │
│  TITLE      : Package init and single-sourced version                       │
│  DEPENDS ON : CK-0001                                                       │
│  NEXT       : CK-0003                                                       │
│  FILES      : src/contextkeel/__init__.py                                   │
│               src/contextkeel/__about__.py                                  │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

`__about__.py` holds `__version__ = "0.1.0"` and nothing else — it is the single
source of truth read by both hatchling and `ckeel --version`.

`__init__.py` re-exports `__version__` and the small public surface other code
imports. Keep it free of side effects: no config loading, no filesystem access,
no subprocess calls at import time.

[VERIFY] `python -c "import contextkeel; print(contextkeel.__version__)"` prints 0.1.0.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0003                                                       │
│  SCOPE      : S1 — Package Foundation                                       │
│  TITLE      : Exception hierarchy with user-safe messages                   │
│  DEPENDS ON : CK-0002                                                       │
│  NEXT       : CK-0004                                                       │
│  FILES      : src/contextkeel/errors.py                                     │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Define the error types every other module raises. Each carries two messages: a
developer-facing `str(exc)` with full detail, and a `user_message` property that
is short, actionable, and obeys the vocabulary rule in the CODING RULES header.

- `ContextkeelError` (base) — holds `user_message`, defaults to a generic line.
- `ToolchainError` — Python/uv/self missing or unusable.
- `BackendUnavailable` — a code-index backend can't run. Its `user_message` is
  neutral in the default register; the full detail (backend name, version,
  failing command) is always present on the exception and is surfaced verbatim
  in expert mode. Degrade silently by default (see CK-0016), never opaquely.
- `RenderConflict` — a generated file was edited by hand and would be clobbered.
- `VaultError` — vault tree is missing or malformed.
- `StateError` — `.contextkeel/state.json` is corrupt or from a future schema.

Never raise bare `Exception`; never use bare `except:`.

[VERIFY] `pytest tests/test_errors.py` — every subclass exposes a non-empty user_message.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0004                                                       │
│  SCOPE      : S1 — Package Foundation                                       │
│  TITLE      : ★ Cross-platform primitives                                   │
│  DEPENDS ON : CK-0003                                                       │
│  NEXT       : CK-0005                                                       │
│  FILES      : src/contextkeel/platform.py                                   │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Every OS difference in the codebase lives here and nowhere else. Anything that
branches on the operating system outside this module is a bug.

- `class OS(StrEnum)`: `MACOS`, `WINDOWS`, `LINUX`; `current_os()`.
- `user_bin_dir()` — `~/.local/bin` on POSIX, `%USERPROFILE%\.local\bin` on
  Windows (this is where `uv tool install` puts shims).
- `ensure_on_path(directory)` — appends to the user's PATH persistently:
  `setx` on Windows, the right rc file on POSIX. Idempotent, never duplicates.
- `executable_name(stem)` — appends `.exe` on Windows.
- `run(cmd, *, timeout, cwd)` — the ONLY subprocess wrapper. Forces
  `encoding="utf-8"`, `errors="replace"` (Windows consoles default to cp1252
  and will raise UnicodeDecodeError on tool output otherwise), never uses
  `shell=True`, always passes a list, always sets a timeout. Returns a
  `CompletedProcess`-like dataclass with `ok`, `out`, `err`, `code`.

All paths are `pathlib.Path`. No `os.path`, no string concatenation of paths.

[VERIFY] `pytest tests/test_platform.py` passes on all three OSes in CI (CK-0045).

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0005                                                       │
│  SCOPE      : S1 — Package Foundation                                       │
│  TITLE      : Console output and the vocabulary guard                       │
│  DEPENDS ON : CK-0004                                                       │
│  NEXT       : CK-0006                                                       │
│  FILES      : src/contextkeel/console.py                                    │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

All user-facing output goes through this module. It implements **two registers**
of the same information — the product's promise is that a developer never *has*
to learn an internal tool's name, not that they are prevented from doing so.

- `step()`, `say()`, `ok()`, `warn()`, `fail()` — plain, no colour dependency.
  Respect global `--quiet`, `--json`, and `--expert` modes set by the CLI.
- `INTERNAL_TERMS = {"graphify": "code index", "graphifyy": "code index",
  "obsidian": "notes viewer"}` — the mapping between the two registers, not a
  blocklist. Keep it importable: CK-0038A prints it and CK-0042 asserts on it.
- `render(text)` — in the DEFAULT register, case-insensitively rewrites internal
  terms to their neutral equivalent. In the EXPERT register, passes text through
  untouched, so real names, versions, and command lines appear verbatim.
- Surfaced subprocess output goes through the same function, so it follows
  whichever register is active rather than leaking by accident.
- `--json` output is ALWAYS the expert register: a machine consumer parsing
  "code index" instead of the real backend id is broken by design.
- Debug logging via stdlib `logging` always records real names regardless of
  register — it is written to file, never to the terminal.

[VERIFY] `pytest tests/test_console.py` — scrub() rewrites every banned term in mixed case.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0006                                                       │
│  SCOPE      : S1 — Package Foundation                                       │
│  TITLE      : ★ project.yml model, auto-detection, and defaults             │
│  DEPENDS ON : CK-0005                                                       │
│  NEXT       : CK-0007                                                       │
│  FILES      : src/contextkeel/config.py                                     │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Pydantic v2 model mirroring the `project.yml` schema this template already
defines (project/frontend/backend/architecture/ui/conventions/context/defaults).

- `load(path)` / `save(model, path)` using `ruamel.yaml` in round-trip mode so
  the extensive comments in project.yml survive a write.
- `resolve()` — for every field that is `auto` or empty, detect from manifests:
  `package.json` (+ deps for framework/platform), `pyproject.toml`,
  `*.csproj`, `Cargo.toml`, `go.mod`, lockfiles, `pnpm-workspace.yaml`,
  `turbo.json`, `nx.json`. Detection order and rules are exactly those in
  `AGENTS.md` §3.
- If detection finds nothing, fall back to the `defaults:` sub-block.
- **Never raise on a missing or malformed project.yml** — synthesise one from
  `defaults` and carry on. Blocking a developer on config is the one thing this
  product must never do.
- `resolve()` is pure: it returns a resolved model, it does not write. The CLI
  decides whether to persist.

[VERIFY] `pytest tests/test_config.py` — fixtures for node/python/go/dotnet repos each resolve correctly, and an empty repo resolves to defaults.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0007                                                       │
│  SCOPE      : S1 — Package Foundation                                       │
│  TITLE      : Workspace discovery and path layout                           │
│  DEPENDS ON : CK-0006                                                       │
│  NEXT       : CK-0008                                                       │
│  FILES      : src/contextkeel/paths.py                                      │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Resolves where everything lives, for any repo on any OS.

- `find_repo_root(start)` — walk up for `.git`, then for `project.yml`, then
  fall back to `start`. Never returns a path outside the user's tree.
- `workspace_dir(root)` → `root / ".contextkeel"` (state, index output, logs).
- `index_dir(root)` → `.contextkeel/index/` (REPORT.md, index.json).
- `vault_dir(root)` → configurable via project.yml `context.vault`, default
  `root / "Vault"`.
- `docs_dir(root)` → `root / ".docs"`.
- `cache_dir()` — per-user, per-OS, via `platformdirs.user_cache_dir("contextkeel")`.

Add `.contextkeel/` to the repo's `.gitignore` on first init (append, don't
rewrite; skip if already present).

[VERIFY] `pytest tests/test_paths.py` — discovery works from a nested subdirectory and in a repo with no .git.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0008                                                       │
│  SCOPE      : S1 — Package Foundation                                       │
│  TITLE      : Durable state file                                            │
│  DEPENDS ON : CK-0007                                                       │
│  NEXT       : CK-0009                                                       │
│  FILES      : src/contextkeel/state.py                                      │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

`.contextkeel/state.json` — what the tool knows between runs.

Fields: `schema_version` (int), `contextkeel_version`, `selected_backend`,
`backend_degraded` (bool + reason), `last_sync` (ISO timestamp + git sha),
`rendered_fingerprints` (path → sha256 of the content this tool generated),
`viewer_installed` (tri-state: yes / no / not-attempted).

- Atomic writes (temp file + `Path.replace`) so a crash never corrupts it.
- `load()` tolerates a missing file (returns defaults) and a corrupt one
  (backs it up to `state.json.bak`, returns defaults, logs a warning) — it must
  never crash the CLI.
- Raise `StateError` only when `schema_version` is *newer* than this build
  understands; tell the user to upgrade.
- `rendered_fingerprints` is what makes hand-edit detection (CK-0029) possible.

[VERIFY] `pytest tests/test_state.py` — corrupt JSON round-trips to defaults plus a .bak file.

════════════════════════════════════════════════════════════════════════════════
SCOPE 2 — ZERO-FRICTION BOOTSTRAP
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0009                                                       │
│  SCOPE      : S2 — Zero-Friction Bootstrap                                  │
│  TITLE      : ★ POSIX bootstrap installer                                   │
│  DEPENDS ON : CK-0008                                                       │
│  NEXT       : CK-0010                                                       │
│  FILES      : bootstrap/install.sh                                          │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

The single line a macOS/Linux developer runs. Everything else in this product is
downstream of this file working on a machine with nothing installed.

`curl -LsSf https://contextkeel.dev/install.sh | sh`

- Target POSIX `sh`, not bash — `/bin/sh` on Debian is dash and bash-isms break.
- Steps, each skipped if already satisfied: ensure Python 3.11+ (brew on macOS,
  apt/dnf/pacman/zypper on Linux, with a clear manual-install URL if none of
  them exist) → install `uv` via the official astral installer → `uv tool
  install contextkeel` → add `~/.local/bin` to PATH → run `ckeel init --auto`.
- Fully non-interactive: no prompts, no pagers, no sudo unless a system package
  manager genuinely needs it (and say so on the line before).
- Prints at most 6 lines total. Never prints the name of any internal tool.
- Exits non-zero on hard failure with exactly one actionable sentence.
- Idempotent: running it twice on a working machine changes nothing.

[VERIFY] In a fresh Docker container (`python:3.11-slim` and `ubuntu:22.04` with no Python), `sh install.sh` ends with a working `ckeel --version`.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0010                                                       │
│  SCOPE      : S2 — Zero-Friction Bootstrap                                  │
│  TITLE      : ★ Windows bootstrap installer                                 │
│  DEPENDS ON : CK-0009                                                       │
│  NEXT       : CK-0011                                                       │
│  FILES      : bootstrap/install.ps1                                         │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

The Windows equivalent of CK-0009, invoked as:

`irm https://contextkeel.dev/install.ps1 | iex`

- Must work on Windows PowerShell 5.1 (still the default on many machines) and
  PowerShell 7+. Avoid 7-only syntax such as `??`, `?.`, and ternaries.
- Ensure Python 3.11+ via `winget install Python.Python.3.12`, falling back to
  the python.org installer URL if winget is unavailable. Never rely on the
  Microsoft Store alias stub (`python.exe` that opens the Store) — detect and
  reject it explicitly, that trap silently breaks installs.
- Install `uv` via `irm https://astral.sh/uv/install.ps1 | iex`.
- `uv tool install contextkeel`, then persist `%USERPROFILE%\.local\bin` to the
  user PATH with `setx` (not just the current session).
- Run `ckeel init --auto`.
- Same constraints as CK-0009: non-interactive, <= 6 lines of output, no
  internal tool names, one actionable sentence on failure, idempotent.
- Set `$ErrorActionPreference = "Stop"` and wrap in try/catch.

[VERIFY] On a clean Windows VM/runner with no Python, the one-liner ends with a working `ckeel --version`.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0011                                                       │
│  SCOPE      : S2 — Zero-Friction Bootstrap                                  │
│  TITLE      : Programmatic toolchain repair                                 │
│  DEPENDS ON : CK-0010                                                       │
│  NEXT       : CK-0012                                                       │
│  FILES      : src/contextkeel/bootstrap/toolchain.py                        │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

The same logic as the two bootstrap scripts, callable from Python, so that
`ckeel doctor --fix` can repair a broken machine without the user re-running
the installer.

- `ensure_python()`, `ensure_uv()`, `ensure_self_on_path()` — each returns a
  `CheckResult(ok, detail, fixed)`.
- Reuse `platform.run()` for every subprocess; never shell out directly.
- Detect the Windows Store python stub and treat it as *missing*.
- Each function is idempotent and safe to call when everything is fine.

Keep this module and the shell scripts behaviourally identical — CK-0044
asserts they agree.

[VERIFY] `pytest tests/test_toolchain.py` with a faked PATH — each ensure_* is a no-op when the tool is present.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0012                                                       │
│  SCOPE      : S2 — Zero-Friction Bootstrap                                  │
│  TITLE      : Self-upgrade and state migration                              │
│  DEPENDS ON : CK-0011                                                       │
│  NEXT       : CK-0013                                                       │
│  FILES      : src/contextkeel/bootstrap/selfupdate.py                       │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

- `upgrade()` — runs `uv tool upgrade contextkeel`, then re-runs the render step
  so an upgraded package refreshes the agent configs it generated.
- `migrate_state(state)` — stepwise migrations keyed on `schema_version`, each a
  small pure function. Never destructive: back up before migrating.
- `check_for_update()` — best-effort, cached for 24h in `paths.cache_dir()`,
  fully silent on network failure. Never blocks a command.

[VERIFY] `ckeel upgrade --dry-run` reports the target version without mutating anything.

════════════════════════════════════════════════════════════════════════════════
SCOPE 3 — CODE-INDEX BACKENDS
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0013                                                       │
│  SCOPE      : S3 — Code-Index Backends                                      │
│  TITLE      : ★ Backend-neutral index interface                             │
│  DEPENDS ON : CK-0012                                                       │
│  NEXT       : CK-0014                                                       │
│  FILES      : src/contextkeel/graph/base.py                                 │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

The abstraction that removes the single point of failure. No type or field name
in this file may reference a specific third-party tool.

- `class GraphBackend(Protocol)`: `name: str`, `is_available() -> bool`,
  `build(root) -> IndexResult`, `update(root) -> IndexResult`,
  `query(q: str) -> list[Node]`, `priority: int`.
- Neutral dataclasses: `Node` (id, kind, path, name, line), `Edge` (src, dst,
  kind), `Community` (id, label, members), `IndexResult` (nodes, edges,
  communities, stats, backend_name, generated_at).
- All collections sorted deterministically on construction so the golden tests
  in CK-0042 are stable across runs and platforms.
- Backends raise `BackendUnavailable` — they never call `sys.exit` and never
  print. Presentation is the caller's job.

[VERIFY] `pytest tests/test_graph_base.py` — a stub backend satisfies the Protocol under `typing.runtime_checkable`.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0014                                                       │
│  SCOPE      : S3 — Code-Index Backends                                      │
│  TITLE      : Default backend adapter                                       │
│  DEPENDS ON : CK-0013                                                       │
│  NEXT       : CK-0015                                                       │
│  FILES      : src/contextkeel/graph/graphify_backend.py                     │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Wraps the preferred third-party indexer as one implementation of `GraphBackend`.

- `is_available()` — probe for the CLI; if absent, attempt a one-time quiet
  install via `uv tool install`, cached in state so it is never retried in a
  loop. Any failure returns False rather than raising.
- Probe the installed version and its supported flags once, cache the result;
  do not assume flag names are stable across releases.
- `build()` runs a full extraction; `update()` runs the incremental path and
  falls back to a full build if the incremental flag is unsupported.
- Parse the tool's output into the neutral dataclasses from CK-0013. Do not let
  its native schema leak past this file.
- Hard timeout on every call. On timeout, non-zero exit, or unparseable output:
  raise `BackendUnavailable` with the detail in the developer message only.

[VERIFY] `pytest tests/test_graphify_backend.py` with a faked CLI — happy path parses, and each failure mode raises BackendUnavailable.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0015                                                       │
│  SCOPE      : S3 — Code-Index Backends                                      │
│  TITLE      : ★ Bundled offline fallback indexer                            │
│  DEPENDS ON : CK-0014                                                       │
│  NEXT       : CK-0016                                                       │
│  FILES      : src/contextkeel/graph/fallback_backend.py                     │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

The reason the promise survives upstream breakage. Ships inside the package and
needs no network and no external binary.

- Walk the repo with `pathlib`, honouring `.gitignore` (parse it; do not shell
  out to git, which may be absent).
- Parse each supported source file with `tree-sitter-language-pack` and extract
  module/class/function definitions plus import statements.
- Build edges from imports: file → imported module, resolved to in-repo paths
  where possible.
- Derive rough communities by directory grouping — good enough for navigation;
  this is a graceful degradation, not a competitor.
- Emit the same `IndexResult` as every other backend.
- `is_available()` returns True whenever the tree-sitter extra imported cleanly;
  if even that fails, degrade again to a filename/import regex scan rather than
  raising. There must always be *some* index.
- Cap work on very large repos (file count and size limits) and record the cap
  in `IndexResult.stats` so `doctor` can mention it.

[VERIFY] `pytest tests/test_fallback_backend.py` — indexes the python/node fixture repos offline (`-m 'not network'`) and finds known symbols.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0016                                                       │
│  SCOPE      : S3 — Code-Index Backends                                      │
│  TITLE      : ★ Backend selection and silent degradation                    │
│  DEPENDS ON : CK-0015                                                       │
│  NEXT       : CK-0017                                                       │
│  FILES      : src/contextkeel/graph/registry.py                             │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

- Ordered registry by `priority`; `select()` returns the first backend whose
  `is_available()` is True, and records the choice in state.
- **Degradation is silent by design.** If the preferred backend disappears, the
  next one engages and normal command output is byte-for-byte unchanged. Only
  `ckeel doctor` mentions it, and only as "using the built-in indexer".
- Cache the selection in `state.selected_backend`; re-probe when the package
  version changes or `--refresh-backends` is passed.
- **`--backend <name>` is a documented, supported option**, not a hidden debug
  flag: an expert who wants a specific indexer selects it and the tool obeys.
  It can also be pinned in `project.yml` under `context.backend` so the choice
  survives across machines and teammates.
- `--refresh-backends` re-probes on demand.
- Record `backend_degraded` + reason in state. In the default register the
  degradation stays quiet; in expert mode (and in `ckeel internals`, CK-0038A)
  it reports which backend was chosen, which was skipped, and exactly why.

[VERIFY] `pytest tests/test_registry.py` — with the default backend forced unavailable, select() returns the fallback and stdout is identical to the non-degraded run.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0017                                                       │
│  SCOPE      : S3 — Code-Index Backends                                      │
│  TITLE      : Index report rendering                                        │
│  DEPENDS ON : CK-0016                                                       │
│  NEXT       : CK-0018                                                       │
│  FILES      : src/contextkeel/graph/report.py                               │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Turn an `IndexResult` into what agents actually read.

- `.contextkeel/index/REPORT.md` — architecture overview, module/community list,
  the most-connected nodes ("start here"), and per-area entry points. Written
  for an agent deciding which files to open, so lead with navigation, not stats.
- `.contextkeel/index/index.json` — the full neutral graph for precise queries.
- Deterministic ordering and stable formatting; no timestamps inside the body
  (put `generated_at` in a single header line) so golden diffs stay readable.
- Include a short header telling the agent to query this instead of globbing.

[VERIFY] Running the renderer twice on an unchanged repo produces byte-identical files apart from the header timestamp.

════════════════════════════════════════════════════════════════════════════════
SCOPE 4 — VAULT — PRESCRIPTIVE CONTEXT
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0018                                                       │
│  SCOPE      : S4 — Vault — Prescriptive Context                             │
│  TITLE      : Vault scaffolding                                             │
│  DEPENDS ON : CK-0017                                                       │
│  NEXT       : CK-0019                                                       │
│  FILES      : src/contextkeel/vault/scaffold.py                             │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Create the prescriptive-context tree, idempotently and non-destructively.

- Tree: `Home.md`, `Changelog.md`, `Context/{Tech Stack,Architecture,
  Conventions,Domain Glossary,API Contracts}.md`, `Decisions/`, `Knowledge/`,
  `Daily/`, `Inbox/`, `Templates/`, `attachments/`.
- **Never overwrite a file the user or an agent has edited.** Compare against
  `state.rendered_fingerprints`: unchanged since we wrote it → safe to refresh;
  changed → leave it and report drift.
- Creating the vault must work with no viewer app installed — it is plain
  markdown and nothing here may depend on the optional viewer.

[VERIFY] `pytest tests/test_vault_scaffold.py` — second run is a no-op; a hand-edited note survives a re-scaffold.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0019                                                       │
│  SCOPE      : S4 — Vault — Prescriptive Context                             │
│  TITLE      : Bundled vault templates with real substitution                │
│  DEPENDS ON : CK-0018                                                       │
│  NEXT       : CK-0020                                                       │
│  FILES      : src/contextkeel/vault/templates/                              │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Ship every starter note as package data, rendered through Jinja2.

- Port the existing notes from this template repo's `Vault/` as the starting
  content, with project-specific values parameterised.
- Substitute real values for `title`, `date`, `time`, project name, and stack.
  **No literal `{{ ... }}` token may survive into a written file** — that is a
  visible bug and CK-0042 asserts against it.
- Include `Templates/` (ADR, Module Note, Feature Spec, Daily Dev Log,
  Permanent Note) — those are user-facing templates and are the one place
  placeholder tokens are legitimate, so exclude that directory from the
  no-tokens assertion.
- Seed `Decisions/0001` explaining the context system, generated with today's
  real date.

[VERIFY] `pytest tests/test_vault_templates.py` — grep every rendered file outside Templates/ for `{{`; expect zero hits.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0020                                                       │
│  SCOPE      : S4 — Vault — Prescriptive Context                             │
│  TITLE      : Section-level note updates                                    │
│  DEPENDS ON : CK-0019                                                       │
│  NEXT       : CK-0021                                                       │
│  FILES      : src/contextkeel/vault/notes.py                                │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Agents and `sync` update these notes repeatedly, so updates must merge, not
clobber.

- Parse a note into frontmatter + a list of `## Section` blocks.
- `upsert_section(note, heading, body)` — replace one section, preserve
  everything else including the user's own added sections.
- Typed helpers: `set_tech_stack(resolved_config)`, `upsert_api_contract(...)`,
  `add_glossary_term(term, definition)` (alphabetical insert, no duplicates).
- Preserve frontmatter fields the tool does not own.
- Round-trip safe: parse → write with no edits produces an identical file.

[VERIFY] `pytest tests/test_notes.py` — a hand-added section survives an upsert of a different section.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0021                                                       │
│  SCOPE      : S4 — Vault — Prescriptive Context                             │
│  TITLE      : Changelog entries and ADR allocation                          │
│  DEPENDS ON : CK-0020                                                       │
│  NEXT       : CK-0022                                                       │
│  FILES      : src/contextkeel/vault/changelog.py                            │
│               src/contextkeel/vault/adr.py                                  │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

- `prepend_entry(title, sentences)` — insert `## YYYY-MM-DD — Title` plus 1-3
  plain sentences directly below the Changelog's intro block, newest first.
  Never append at the bottom. Refuse entries containing file paths or diff
  fragments — this note is for a human catching up.
- `next_adr_number()` — scan `Decisions/` for the highest `NNNN-` prefix and
  return the next, zero-padded to 4. Handle gaps and the empty directory.
- `create_adr(title, context, decision, consequences, alternatives)` — render
  from the ADR template with a real date and a slugified filename.
- Both use the repo's local date, not UTC, so entries match the developer's day.

[VERIFY] `pytest tests/test_changelog.py` — two entries land newest-first; ADR numbering skips no codes and handles an empty Decisions/.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0022                                                       │
│  SCOPE      : S4 — Vault — Prescriptive Context                             │
│  TITLE      : Optional viewer — best-effort and silent                      │
│  DEPENDS ON : CK-0021                                                       │
│  NEXT       : CK-0023                                                       │
│  FILES      : src/contextkeel/vault/viewer.py                               │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Installs the optional notes viewer. This is the module where "never bother the
developer" is most easily violated, so the constraints are strict.

- Attempt order: macOS `brew install --cask`, Windows `winget install`, Linux
  `flatpak install` — each only if that manager is already present.
- Hard timeout (60s). All stdout/stderr swallowed. **Never prompts. Never
  prints. Never fails a command it is part of.**
- Attempted at most once per machine; record `viewer_installed` in state as
  yes / no / not-attempted so it is not retried on every init.
- Skip entirely when headless (no `DISPLAY`/`WAYLAND_DISPLAY` on Linux) or when
  `CI` is set — installing a GUI app in CI is pure waste.
- `doctor` reports it as an optional line; its absence is never a warning.
- **Explicit control for anyone who wants it**, overriding all of the above:
  `ckeel init --with-viewer` forces the attempt (and reports failure normally
  instead of silently), `--no-viewer` skips it permanently, and
  `context.viewer: always | auto | never` in `project.yml` pins the policy.
  An expert who wants the notes app should never have to fight the default.

[VERIFY] `pytest tests/test_viewer.py` — with every package manager faked as absent, install() returns cleanly, prints nothing, and records not-attempted.

════════════════════════════════════════════════════════════════════════════════
SCOPE 5 — AGENT-CONFIG RENDERING
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0023                                                       │
│  SCOPE      : S5 — Agent-Config Rendering                                   │
│  TITLE      : ★ Canonical agent-config model                                │
│  DEPENDS ON : CK-0022                                                       │
│  NEXT       : CK-0024                                                       │
│  FILES      : src/contextkeel/render/model.py                               │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

One model that every tool's config is generated from. This is what makes the
~50-file mirror-drift problem structurally impossible.

- `SkillDef` (name, description, body, `model_invocable: bool`),
  `CommandDef` (name, description, body), `RuleDef` (name, description, globs,
  body, `always_apply: bool`), `McpServerDef` (name, command, args, env),
  `HookDef` (event, matcher, command), `AgentDef` (name, description, tools, body).
- `TargetCapabilities` per tool: does it support glob-scoped rules? nested
  skills? a per-skill invocation flag? which frontmatter dialect? where does
  MCP config live?
- The model is tool-agnostic: no field may exist solely because one IDE wants
  it. Tool-specific shaping happens in the target renderers (CK-0025..0027).

[VERIFY] `pytest tests/test_render_model.py` — models validate and reject unknown fields (`extra="forbid"`).

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0024                                                       │
│  SCOPE      : S5 — Agent-Config Rendering                                   │
│  TITLE      : ★ The single canonical content source                         │
│  DEPENDS ON : CK-0023                                                       │
│  NEXT       : CK-0025                                                       │
│  FILES      : src/contextkeel/render/content/                               │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

The one copy of every skill, command, rule, and agent definition, as package
data. Today this content exists three times across `.cursor/`, `.claude/`, and
`.continue/`; here it exists once.

- Port all 16 skills, 10 commands, 8 rules, and 3 agent definitions from this
  template repo, deduplicated into a single set of markdown/YAML sources.
- Resolve the asymmetry found in the audit: 14 of 16 Cursor skills currently
  carry `disable-model-invocation` while only 2 Claude skills do. Set
  `model_invocable` **once** here — False only for `load-context` and
  `update-context` (they are explicit workflow entry points), True for the rest.
- Rewrite the Continue prompt bodies so they are self-contained: they currently
  say "read `.cursor/skills/...`", which breaks whenever `.cursor/` is absent.
- Write the content in the neutral vocabulary from CK-0005, and add one line to
  the generated `AGENTS.md` telling the reader that `ckeel internals` names
  every underlying tool and prints the exact commands. Neutral by default,
  never a dead end.

[VERIFY] `pytest tests/test_content.py` — every source parses into a model from CK-0023, and no body references another tool's directory.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0025                                                       │
│  SCOPE      : S5 — Agent-Config Rendering                                   │
│  TITLE      : Claude Code target renderer                                   │
│  DEPENDS ON : CK-0024                                                       │
│  NEXT       : CK-0026                                                       │
│  FILES      : src/contextkeel/render/targets/claude.py                      │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Emit `.claude/` from the canonical model.

- `CLAUDE.md` — thin shim pointing at `AGENTS.md`, `project.yml`, the index dir,
  and the vault, with paths resolved for this repo.
- `skills/<name>/SKILL.md` — frontmatter `name`, `description`, and
  `disable-model-invocation: true` only where `model_invocable` is False.
- `commands/<name>.md` with a `description` frontmatter field.
- `agents/<name>.md` with `name`, `description`, `tools`.
- `settings.json` — permissions and hooks. The allow-list must cover the
  commands this product's own workflow requires (`ckeel`, `uv`, the project's
  test runner from resolved config) so the developer is not prompted for the
  tool's own operation. Deny-list covers `**/.env`, `**/.env.*`, `**/*.secret`.

[VERIFY] `ckeel init` in a fixture repo produces a `.claude/` tree that Claude Code loads without warnings.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0026                                                       │
│  SCOPE      : S5 — Agent-Config Rendering                                   │
│  TITLE      : Cursor target renderer                                        │
│  DEPENDS ON : CK-0025                                                       │
│  NEXT       : CK-0027                                                       │
│  FILES      : src/contextkeel/render/targets/cursor.py                      │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Emit `.cursor/` from the same model.

- `rules/*.mdc` with Cursor's frontmatter dialect: `description`, unquoted
  `globs`, `alwaysApply`. Only `00-core` is always-applied.
- `skills/<name>/SKILL.md`, `commands/<name>.md`, `hooks.json` (afterFileEdit),
  `mcp.json` (delegated to CK-0028).
- Honour `TargetCapabilities`: Cursor supports glob-scoped rules, so the
  language idiom rules render here as real rule files.
- Same `model_invocable` values as every other target — no per-tool drift.

[VERIFY] Golden test in CK-0042 — rendered `.cursor/rules/lang-python.mdc` matches the expected frontmatter shape exactly.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0027                                                       │
│  SCOPE      : S5 — Agent-Config Rendering                                   │
│  TITLE      : Continue target renderer                                      │
│  DEPENDS ON : CK-0026                                                       │
│  NEXT       : CK-0028                                                       │
│  FILES      : src/contextkeel/render/targets/continue_.py                   │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Emit `.continue/` from the same model.

- `config.yaml` — name, schema, context providers, and one `prompts:` entry per
  command. Leave `models:` commented out: API keys are per-person and must
  never be generated into a shared file.
- `rules/*.md` — Continue's frontmatter dialect (`name`, `description`,
  **quoted** `globs`), mirroring the same rule content Cursor gets.
- `mcpServers/mcp.json` — delegated to CK-0028.
- **Self-containment is the point of this prompt:** every prompt body must
  inline the instruction it needs or reference a path inside `.continue/`.
  Referencing `.cursor/` is a build error, and CK-0042 asserts it.

[VERIFY] Golden test — grep the rendered `.continue/` tree for the string `.cursor/`; expect zero hits.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0028                                                       │
│  SCOPE      : S5 — Agent-Config Rendering                                   │
│  TITLE      : ★ MCP config generation with resolved paths                   │
│  DEPENDS ON : CK-0027                                                       │
│  NEXT       : CK-0029                                                       │
│  FILES      : src/contextkeel/render/mcp.py                                 │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

This prompt exists specifically to make the bug found in the audit impossible:
three checked-in MCP files hardcoding one developer's `D:\Learnings\Template`
path, broken on every other machine.

- Build the server list from `McpServerDef`s, resolving every path at render
  time from `paths.find_repo_root()` — never from a literal, never from a
  captured value baked in at package build time.
- Emit correct separators and escaping per OS (JSON-escaped backslashes on
  Windows). Serialise `Path` objects through one helper, not by `str()` at call
  sites.
- Servers: the contextkeel MCP server (CK-0039), plus filesystem scoped to the
  vault, and fetch. Point the git server at the resolved repo root.
- One function produces the dict; all three targets serialise the same dict, so
  the three files cannot disagree.
- Regenerate on every `init`/`sync`, so moving or renaming the repo self-heals.

[VERIFY] `pytest tests/test_mcp_render.py` — render under a temp root, assert every path in the output is inside that root and no foreign absolute path appears. Then move the fixture repo and assert `sync` rewrites the paths.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0029                                                       │
│  SCOPE      : S5 — Agent-Config Rendering                                   │
│  TITLE      : ★ Render orchestration, atomic writes, drift detection        │
│  DEPENDS ON : CK-0028                                                       │
│  NEXT       : CK-0030                                                       │
│  FILES      : src/contextkeel/render/engine.py                              │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

- `render(root, *, check=False)` — run every target renderer, then either write
  or report.
- Atomic writes via temp file + `Path.replace`; never leave a half-written
  config if the process dies.
- After each write, record the content sha256 in `state.rendered_fingerprints`.
- Before overwriting, compare the on-disk sha to the recorded fingerprint:
  - matches → safe, rewrite.
  - differs → the user hand-edited a generated file. Do not clobber. Collect a
    `RenderConflict` and report it through `doctor`, suggesting they move the
    change into the canonical source instead.
- `check=True` writes nothing and returns a drift report — this is what the CI
  workflow (CK-0048) and `sync --check` call.

[VERIFY] `pytest tests/test_render_engine.py` — hand-edit a generated file, re-render, assert it is preserved and reported as drift.

════════════════════════════════════════════════════════════════════════════════
SCOPE 6 — AUTO-SYNC HOOKS
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0030                                                       │
│  SCOPE      : S6 — Auto-Sync Hooks                                          │
│  TITLE      : Hook payload definitions                                      │
│  DEPENDS ON : CK-0029                                                       │
│  NEXT       : CK-0031                                                       │
│  FILES      : src/contextkeel/hooks/payloads.py                             │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Hook bodies as data, so they render into each tool's own config format.

- `tidy-markdown` — post-edit, normalises whitespace in written markdown.
- `sync-index` — fires after edits to source files; debounced.
- `sync-on-stop` — fires when an agent session ends; runs the full sync so
  context is fresh for the next session **without the agent having to remember**.
  This hook is the mechanism behind the product's core promise.
- Commands are always `ckeel _hook <name>`, never a path to a script file.
  A shim on PATH works identically on all three OSes; a `node path/to.js`
  command (as the current template uses) breaks the moment Node is absent or
  the repo moves.

[VERIFY] `pytest tests/test_hook_payloads.py` — every payload's command is a `ckeel _hook` invocation with no absolute paths.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0031                                                       │
│  SCOPE      : S6 — Auto-Sync Hooks                                          │
│  TITLE      : Hook installation via the render engine                       │
│  DEPENDS ON : CK-0030                                                       │
│  NEXT       : CK-0032                                                       │
│  FILES      : src/contextkeel/hooks/install.py                              │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Hooks are stamped into `.claude/settings.json` and `.cursor/hooks.json` through
the same render engine as everything else, so they inherit atomic writes,
fingerprinting, and drift detection and cannot silently diverge.

- Merge into an existing settings file rather than replacing it: preserve
  user-authored hooks and permissions, add or update only the ones this tool owns
  (tag them so they are identifiable on re-render).
- Continue has no hook system today — record that in `TargetCapabilities` and
  skip it without warning rather than emitting a broken config.

[VERIFY] `ckeel init` twice — user-added hooks and permissions in settings.json survive both runs.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0032                                                       │
│  SCOPE      : S6 — Auto-Sync Hooks                                          │
│  TITLE      : ★ Hidden hook runner — fails open, always                     │
│  DEPENDS ON : CK-0031                                                       │
│  NEXT       : CK-0033                                                       │
│  FILES      : src/contextkeel/hooks/runner.py                               │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

The `ckeel _hook <name>` entry point (hidden from `--help`). It runs on every
file edit in every agent session, so its failure modes matter more than its
features.

- **Always exits 0.** Always writes valid JSON (`{}`) to stdout. Any exception
  is caught, logged to `.contextkeel/logs/hooks.log`, and swallowed. A hook that
  breaks a developer's edit loop is a catastrophic failure of the product
  promise; a hook that silently does nothing is merely a missed optimisation.
- Hard wall-clock timeout (default 5s). Exceeding it aborts the work, not the
  edit.
- **Debounce**: record the last run in `.contextkeel/state.json`; if a sync ran
  within N seconds, skip. A burst of twenty file writes must trigger one index
  update, not twenty.
- Reads the tool's JSON payload from stdin, tolerating Claude's `tool_input`
  nesting and Cursor's flat shape (the existing template's hook already handles
  both — port that logic).
- Never prints to stdout beyond the JSON envelope; the agent parses it.

[VERIFY] `pytest tests/test_hook_runner.py` — inject a raising handler and assert exit code 0 with `{}` on stdout; assert the debounce suppresses a rapid second call.

════════════════════════════════════════════════════════════════════════════════
SCOPE 7 — CLI SURFACE
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0033                                                       │
│  SCOPE      : S7 — CLI Surface                                              │
│  TITLE      : CLI application shell                                         │
│  DEPENDS ON : CK-0032                                                       │
│  NEXT       : CK-0034                                                       │
│  FILES      : src/contextkeel/cli/main.py                                   │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

- Typer app exposed as both `contextkeel` and `ckeel`.
- Global options: `--quiet`, `--json`, `--version`, `--verbose` (debug logging
  to file, not stdout), `--root` (override repo discovery).
- One top-level exception handler: `ContextkeelError` → print `user_message`
  and exit 1; unexpected exception → generic one-liner plus a log path, full
  traceback to the log file only. A stack trace must never reach the terminal
  in normal use.
- Register the hidden `_hook` command from CK-0032.
- Keep imports lazy so `ckeel --help` stays fast; do not import the indexer at
  module import time.

[VERIFY] `ckeel --help` and `contextkeel --help` both work and list init/doctor/sync/plan/status/upgrade.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0034                                                       │
│  SCOPE      : S7 — CLI Surface                                              │
│  TITLE      : ★ `ckeel init` — the whole product in one command             │
│  DEPENDS ON : CK-0033                                                       │
│  NEXT       : CK-0035                                                       │
│  FILES      : src/contextkeel/cli/init.py                                   │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

The only command most developers will ever type, and the one the bootstrap
scripts call. Everything it needs must be inferred; nothing may be asked.

Sequence: discover root → resolve config (CK-0006, write back the resolved
`project.yml` if it was all `auto`) → scaffold vault (CK-0018) → render all
agent configs (CK-0029) → install hooks (CK-0031) → select backend and build the
index (CK-0016/0017) → best-effort viewer (CK-0022) → write state.

- `--auto` for non-interactive use (the bootstrap path): never prompts, picks
  every default.
- Idempotent: a second `init` on an unchanged repo makes no file changes and
  says so.
- Total output <= 8 lines, ending with one sentence telling the developer what
  to do next. No internal tool names anywhere.
- Partial failure never aborts the whole run: if the index build fails, the
  configs and vault are still written and `doctor` reports the gap.

[VERIFY] `ckeel init --auto` on each fixture repo exits 0; an immediate second run reports no changes.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0035                                                       │
│  SCOPE      : S7 — CLI Surface                                              │
│  TITLE      : ★ `ckeel doctor` — verify and self-repair                     │
│  DEPENDS ON : CK-0034                                                       │
│  NEXT       : CK-0036                                                       │
│  FILES      : src/contextkeel/cli/doctor.py                                 │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

The support surface. When something is wrong, this is the only thing a
developer should ever need to run.

Checks: toolchain (Python, uv, self on PATH) · index backend availability and
whether it is degraded · index freshness vs. the current git sha · rendered
config drift and hand-edit conflicts (CK-0029) · hooks installed and executable ·
vault integrity · optional viewer (informational only, never a warning).

- Each check reports ok / warn / fail with a one-line fix hint.
- `--fix` repairs everything repairable: reinstall toolchain pieces (CK-0011),
  re-render configs, rebuild the index, re-stamp hooks. Never destroys a
  hand-edited file — reports those instead.
- `--json` emits machine-readable output for CI.

[VERIFY] Break each subsystem in a fixture repo (delete hooks, corrupt state, remove the index) and assert `doctor --fix` restores it and exits 0.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0036                                                       │
│  SCOPE      : S7 — CLI Surface                                              │
│  TITLE      : `ckeel sync` — keep context true                              │
│  DEPENDS ON : CK-0035                                                       │
│  NEXT       : CK-0037                                                       │
│  FILES      : src/contextkeel/cli/sync.py                                   │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Called by the stop hook, by CI, and occasionally by hand.

- Incremental index update, falling back to a full build when incremental is
  unavailable or the index is missing.
- Refresh the vault notes that are derived rather than authored: Tech Stack from
  the resolved config; flag API Contracts and Glossary as needing agent
  attention when the index shows new public surface (do not fabricate content —
  detect and report).
- `--check` writes nothing and exits non-zero if the index or configs are stale.
  This is the CI mode.
- `--full` forces a rebuild.
- Under the hook path it must be fast and quiet; under a manual invocation it
  prints a two-line summary.

[VERIFY] Add a source file to a fixture repo, run `ckeel sync`, assert the new symbols appear in `index.json` and that `sync --check` then exits 0.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0037                                                       │
│  SCOPE      : S7 — CLI Surface                                              │
│  TITLE      : ★ `ckeel plan` — prompt-plan generation as a command          │
│  DEPENDS ON : CK-0036                                                       │
│  NEXT       : CK-0038                                                       │
│  FILES      : src/contextkeel/cli/plan.py                                   │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Port the `write-prompt-plan` playbook into real code so the registry format is
guaranteed rather than model-dependent.

- Input: a requirements string or a file, plus the resolved tiers from config.
- Output: `.docs/{frontend,backend,mobile}_prompt_list.md` for applicable tiers
  only, in the exact template format (header block, registry table, boxed
  prompt blocks with aligned borders).
- The box-drawing alignment is computed, never hand-counted.
- `--check` validates an existing plan: every registry code has a matching
  block and vice versa, DEPENDS ON / NEXT pointers resolve, no duplicate codes.
- Retrofit support: `--insert-after CK-0009` allocates `CK-0009A` and fixes the
  neighbouring pointers.

[VERIFY] `ckeel plan --check .docs/backend_prompt_list.md` passes on this very file; corrupt one pointer and assert it fails.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0038                                                       │
│  SCOPE      : S7 — CLI Surface                                              │
│  TITLE      : `ckeel status` — the human summary                            │
│  DEPENDS ON : CK-0037                                                       │
│  NEXT       : CK-0038A                                                      │
│  FILES      : src/contextkeel/cli/status.py                                 │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

A five-line answer to "where is this project?": resolved stack, index freshness,
config drift, pending prompts from `.docs/` registries, and the newest Changelog
entry.

Read-only and fast — no index build, no network, no writes. Safe to wire into a
shell prompt or a status line.

[VERIFY] `ckeel status` on a fixture repo completes in well under a second and writes nothing.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0038A                                                      │
│  SCOPE      : S7 — CLI Surface                                              │
│  TITLE      : ★ Expert mode and escape hatches                              │
│  DEPENDS ON : CK-0038                                                       │
│  NEXT       : CK-0039                                                       │
│  FILES      : src/contextkeel/expert.py                                     │
│               src/contextkeel/cli/internals.py                              │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

RETROFIT (inserted after CK-0038). The counterpart to CK-0005: the default
register keeps a developer from ever needing internal knowledge, and this
prompt guarantees that anyone who *wants* that knowledge gets all of it. The
product hides nothing — it only chooses a sensible default.

- `expert_mode()` is True when ANY of: the `--expert` flag, `CONTEXTKEEL_EXPERT=1`
  in the environment, `--verbose`, or `--json`. Resolved once in
  `cli/main.py` (CK-0033) and read everywhere else; never re-derived ad hoc.
- `ckeel internals` — the full disclosure command. Prints, with real names:
  selected backend, its version and install path, why it was selected and what
  was skipped; the exact command lines this tool runs on the user's behalf;
  index and vault locations; viewer status and policy; every override flag with
  its current effective value and where that value came from (flag, project.yml,
  env, or default).
- It also prints the `INTERNAL_TERMS` mapping from CK-0005, so an expert can
  translate any neutral phrase they have seen in default output back to the
  real tool. That closes the loop: neutral output is never a dead end.
- **Pass-through:** `ckeel index -- <args...>` forwards everything after `--`
  verbatim to the selected backend and streams its raw output. An expert can
  drive the underlying tool directly without abandoning this one.
- Every override is documented in `--help`, not hidden: `--backend`,
  `--with-viewer` / `--no-viewer`, `--refresh-backends`, `--expert`.
- `docs/internals.md` — the written companion: what each backend is, when the
  fallback engages, and how to pin any of it. Linked from the README's
  "Under the hood" section (CK-0047).

Design rule for this prompt: adding an escape hatch must never add a decision
to the default path. A developer who ignores all of this sees exactly the same
output as before it existed.

[VERIFY] `pytest tests/test_expert.py` — default stdout names no internal tool; the identical command under `--expert` names backend and version; `--json` always carries the real backend id; `ckeel index -- --help` reaches the backend's own help.

════════════════════════════════════════════════════════════════════════════════
SCOPE 8 — MCP SERVER
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0039                                                       │
│  SCOPE      : S8 — MCP Server                                               │
│  TITLE      : ★ MCP server                                                  │
│  DEPENDS ON : CK-0038A                                                      │
│  NEXT       : CK-0040                                                       │
│  FILES      : src/contextkeel/mcp/server.py                                 │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Expose the same core to any MCP client, so agents call tools instead of guessing
shell commands. Registered automatically by CK-0028, which means all three IDEs
get it from a single `ckeel init` with no manual configuration.

- stdio transport via the `mcp` package. Launched as `ckeel mcp-serve`.
- Startup must not block: if the index is missing, serve anyway and build lazily
  on first call.
- Errors return structured tool errors, never a crashed server.
- Log to file only — stdout is the protocol channel, and a stray print corrupts
  the stream. This is the single most common way to break an MCP server, so
  route every message through the logger.

[VERIFY] `ckeel mcp-serve` responds correctly to an `initialize` + `tools/list` handshake driven by a test client.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0040                                                       │
│  SCOPE      : S8 — MCP Server                                               │
│  TITLE      : MCP tool definitions                                          │
│  DEPENDS ON : CK-0039                                                       │
│  NEXT       : CK-0041                                                       │
│  FILES      : src/contextkeel/mcp/tools.py                                  │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Tools, each delegating to the exact same functions the CLI calls — no duplicated
logic between the two surfaces:

- `load_context` — resolved stack + index summary + the vault's prescriptive
  notes, in one payload. This is the token-saving primitive: one call replaces
  a dozen file reads at the start of a session.
- `query_index(q)` — symbol/module lookup with file:line results.
- `sync_context` — refresh index and vault.
- `plan(requirements)` — generate or validate the prompt plan.
- `status` — the CK-0038 summary.

Give each a precise JSON schema and a description written for a model deciding
whether to call it. Cap response sizes and paginate `query_index` — an
unbounded dump would defeat the entire purpose of the product.

[VERIFY] `pytest tests/test_mcp_tools.py` — each tool returns schema-valid output against a fixture repo, and query_index paginates.

════════════════════════════════════════════════════════════════════════════════
SCOPE 9 — TESTS & CI
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0041                                                       │
│  SCOPE      : S9 — Tests & CI                                               │
│  TITLE      : Test fixtures and harness                                     │
│  DEPENDS ON : CK-0040                                                       │
│  NEXT       : CK-0042                                                       │
│  FILES      : tests/conftest.py                                             │
│               tests/fixtures/                                               │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

- Fixture repos generated on the fly in `tmp_path`: node+react, python+fastapi,
  go, dotnet, an empty repo, and a monorepo. Each with a real `git init` where
  the test needs a sha.
- `fake_toolchain` fixture — puts stub executables on PATH so backend and
  toolchain paths are testable without installing anything.
- `no_network` autouse fixture — patches the socket module to raise, so any test
  not marked `network` proves the offline path works.
- `frozen_time` for changelog/ADR date assertions.
- Fixtures must construct paths with `pathlib` and never assume `/` — the suite
  runs on Windows in CI.

[VERIFY] `pytest -m 'not network'` collects and passes with no outbound connections.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0042                                                       │
│  SCOPE      : S9 — Tests & CI                                               │
│  TITLE      : ★ Golden render tests and the invariant assertions            │
│  DEPENDS ON : CK-0041                                                       │
│  NEXT       : CK-0043                                                       │
│  FILES      : tests/test_render_golden.py                                   │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

The regression net for the two failure modes that motivated this whole project.

- Golden-file comparison for every rendered target under a fixed fixture repo.
- **Invariant 1 — no foreign paths:** every path in every emitted file resolves
  inside the fixture root. Explicitly assert no `D:\` or `/Users/` literal from
  a developer machine can appear.
- **Invariant 2 — the two registers, asserted in BOTH directions:** (a) default
  output and every generated file contain no term from `console.INTERNAL_TERMS`;
  (b) the SAME commands run with `--expert` DO name the real backend and its
  version, and `--json` always carries the real backend id. A regression that
  silently hides information from an expert must fail the suite just as loudly
  as one that leaks a tool name into the default path.
- **Invariant 3 — no unresolved templates:** no `{{` outside `Vault/Templates/`.
- **Invariant 4 — no cross-tool references:** nothing in `.continue/` mentions
  `.cursor/`.
- **Invariant 5 — consistent flags:** a skill's `model_invocable` value renders
  identically across all targets.
- Update goldens with an explicit `--snapshot-update` flag, never automatically.

[VERIFY] `pytest tests/test_render_golden.py` passes; deliberately reintroduce a hardcoded path and assert the suite fails.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0043                                                       │
│  SCOPE      : S9 — Tests & CI                                               │
│  TITLE      : ★ Degradation tests                                           │
│  DEPENDS ON : CK-0042                                                       │
│  NEXT       : CK-0044                                                       │
│  FILES      : tests/test_graph_degradation.py                               │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Prove the promise holds when the preferred backend is gone.

- Force the default backend unavailable; assert the fallback engages, an index
  is still produced, and `init`/`sync` stdout is byte-identical to the
  non-degraded run.
- Assert `doctor` is the only surface that mentions degradation, and that it
  still uses neutral vocabulary.
- Assert the retry is not attempted on every invocation (state is respected).
- Assert the fallback works with the tree-sitter extra uninstalled, degrading
  once more to the regex scan rather than raising.

[VERIFY] `pytest tests/test_graph_degradation.py` passes with the default backend patched to unavailable.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0044                                                       │
│  SCOPE      : S9 — Tests & CI                                               │
│  TITLE      : ★ End-to-end CLI tests                                        │
│  DEPENDS ON : CK-0043                                                       │
│  NEXT       : CK-0045                                                       │
│  FILES      : tests/test_cli_e2e.py                                         │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

- Full `init → doctor → sync → status` run against every fixture repo.
- **Idempotency:** a second `init` produces zero file modifications (compare a
  full tree hash before and after).
- **Relocation:** move the fixture repo to a new path, run `sync`, assert every
  generated absolute path was rewritten — the failure mode that broke the
  original template.
- **Hand-edit safety:** modify a generated file, re-run `init`, assert it is
  preserved and reported.
- Assert `toolchain.py` and the shell bootstrap scripts agree on what "already
  installed" means.

[VERIFY] `pytest tests/test_cli_e2e.py` passes on Linux, macOS, and Windows runners.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0045                                                       │
│  SCOPE      : S9 — Tests & CI                                               │
│  TITLE      : ★ CI matrix                                                   │
│  DEPENDS ON : CK-0044                                                       │
│  NEXT       : CK-0046                                                       │
│  FILES      : .github/workflows/ci.yml                                      │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

- Matrix: `{ubuntu-latest, macos-latest, windows-latest}` × Python
  `{3.11, 3.12, 3.13}`.
- Steps: install uv → `uv sync` → `ruff check` and `ruff format --check` →
  `pytest -m 'not network'` with coverage.
- A separate job smoke-tests the real bootstrap scripts: `install.sh` in a bare
  `ubuntu:22.04` container with no Python, and `install.ps1` on the Windows
  runner. This job is the only one allowed network access, and it is the one
  that actually validates the product's headline promise.
- Fail the build if coverage on `render/` or `hooks/` drops below 90% — those
  are the modules where a silent regression is most damaging.

[VERIFY] A pull request runs all matrix legs green, including both bootstrap smoke tests.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0046                                                       │
│  SCOPE      : S9 — Tests & CI                                               │
│  TITLE      : Release workflow                                              │
│  DEPENDS ON : CK-0045                                                       │
│  NEXT       : CK-0047                                                       │
│  FILES      : .github/workflows/release.yml                                 │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

- Tag-triggered (`v*`). Build with `uv build`, publish with PyPI **Trusted
  Publishing** (OIDC) — no API token stored in the repository, which is the
  standing rule in the conventions.
- Verify the tag matches `__about__.__version__` and fail loudly if not.
- Post-publish smoke test: in a clean container, run the real one-line installer
  against the just-published version and assert `ckeel --version` matches.
- Attach the bootstrap scripts to the GitHub release so the install URLs can be
  served from a stable location.

[VERIFY] A `v0.1.0` tag publishes to TestPyPI first via a dry-run input, then to PyPI.

════════════════════════════════════════════════════════════════════════════════
SCOPE 10 — DOCS & RELEASE
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0047                                                       │
│  SCOPE      : S10 — Docs & Release                                          │
│  TITLE      : README                                                        │
│  DEPENDS ON : CK-0046                                                       │
│  NEXT       : CK-0048                                                       │
│  FILES      : README.md                                                     │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Written for a developer who will read exactly one screen.

- Opens with the two install lines (POSIX and PowerShell) and nothing before
  them.
- Then one short paragraph on what happens automatically after that.
- Then the command table: `init`, `doctor`, `sync`, `plan`, `status`.
- Then IDE support (Claude Code, Cursor, Continue) — "no configuration
  required" is the message.
- Ends with a short **"Under the hood"** section — the only place in the README
  that names the real indexer and notes app, lists `--backend`, `--with-viewer`,
  `--expert`, and `ckeel internals`, and links to `docs/internals.md`.
  A beginner can stop reading before it; an expert can find everything in it.
  Deep architecture detail still belongs in `docs/`, not here.

[VERIFY] A reader who has never seen the project can install and run it using only the README.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0048                                                       │
│  SCOPE      : S10 — Docs & Release                                          │
│  TITLE      : CI drift-check template for user repos                        │
│  DEPENDS ON : CK-0047                                                       │
│  NEXT       : CK-0049                                                       │
│  FILES      : templates/ci-drift-check.yml                                  │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

The optional workflow `init` stamps into a user's repository so a team's shared
context cannot rot.

- Runs `ckeel sync --check` and `ckeel doctor --json` on pull requests.
- Fails only on real drift: generated configs out of date, or an index stale
  relative to changed source files. Never fails on the optional viewer.
- Scheduled weekly run that opens a PR refreshing the index and vault notes
  rather than committing to the default branch directly.
- `init` writes it only with `--ci` or on explicit confirmation — silently
  adding CI to someone's repo is exactly the kind of surprise this product's
  principle forbids.

[VERIFY] Copy the workflow into a fixture repo with deliberately stale configs; assert the check fails, then passes after `ckeel sync`.

┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT ID  : CK-0049                                                       │
│  SCOPE      : S10 — Docs & Release                                          │
│  TITLE      : LICENSE, changelog, and release checklist                     │
│  DEPENDS ON : CK-0048                                                       │
│  NEXT       : — (end of plan)                                               │
│  FILES      : LICENSE                                                       │
│               CHANGELOG.md                                                  │
│               docs/releasing.md                                             │
│  STATUS     : [x] DONE                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

- `LICENSE` — MIT unless you decide otherwise. The current template has no
  license at all, which technically leaves teammates without permission to use
  it; do not repeat that here.
- `CHANGELOG.md` — Keep a Changelog format, for the package's own releases.
  Distinct from the per-project `Vault/Changelog.md` the tool generates for
  users; say so in a one-line note so the two are never confused.
- `docs/releasing.md` — version bump, tag, publish, verify, announce.

[VERIFY] `ckeel --version`, the git tag, `CHANGELOG.md`, and the PyPI release all agree.
