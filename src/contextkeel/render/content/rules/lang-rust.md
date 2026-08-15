---
name: lang-rust
description: Rust idioms (defers to Vault/Context/Conventions.md)
globs: **/*.rs
always_apply: false
---
# Rust

Follow `Vault/Context/Conventions.md` first. Language idioms:

- Return `Result<T, E>` for fallible work; reserve `panic!`/`unwrap` for truly
  unrecoverable cases and tests.
- Use `?` for propagation; model errors with `thiserror`, surface with `anyhow`
  at the binary boundary.
- Prefer borrowing over cloning; clone only when ownership requires it.
- `snake_case` items, `CamelCase` types, `SCREAMING_SNAKE_CASE` consts.
- Keep modules small; expose a clean `pub` surface.
- `cargo fmt` + `cargo clippy` clean before done; tests via `cargo test`.
- Honor framework from `project.yml` (e.g. axum, actix, tokio runtime).
