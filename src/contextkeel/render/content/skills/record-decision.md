---
name: record-decision
description: Record an architecture decision as an ADR in the vault so the rationale is preserved and consistent for everyone. Use when a non-trivial technical choice is made (framework, pattern, data model, trade-off).
model_invocable: true
---
# Record Decision (ADR)

Capture why a choice was made, not just what.

## Steps
1. Find the next ADR number in `Vault/Decisions/` (zero-padded, e.g. `0002`).
2. Create `Vault/Decisions/<NNNN>-<kebab-title>.md` from
   `Vault/Templates/ADR.md`, filling `{{title}}` and `{{date}}`.
3. Write **Context** (the forces), **Decision** (what we chose), **Consequences**
   (trade-offs/follow-ups), and **Alternatives considered**.
4. Set `status: accepted` (or `proposed` if not yet agreed).
5. Link the ADR from `Vault/Context/Architecture.md` if it affects architecture.

## Quality bar
- One decision per ADR. Keep it under a page.
- Never edit an accepted ADR's decision; supersede it with a new ADR instead.
