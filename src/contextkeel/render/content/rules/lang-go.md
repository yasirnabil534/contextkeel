---
name: lang-go
description: Go idioms (defers to Vault/Context/Conventions.md)
globs: **/*.go
always_apply: false
---
# Go

Follow `Vault/Context/Conventions.md` first. Language idioms:

- Return errors as the last value; wrap with `fmt.Errorf("...: %w", err)`.
- Handle every error explicitly; don't discard with `_` unless intentional.
- Accept interfaces, return structs. Keep interfaces small.
- Use `context.Context` as the first arg for I/O-bound calls.
- `gofmt`/`goimports` clean; `golangci-lint` when configured.
- Package names short and lowercase; exported identifiers documented.
- Tests via `go test ./...`, table-driven where it helps.
- Honor framework from `project.yml` (e.g. gin, echo, chi, stdlib net/http).
