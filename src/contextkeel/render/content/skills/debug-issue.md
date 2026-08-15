---
name: debug-issue
description: Debug a bug or failure systematically using reproduction and runtime evidence before fixing, then add a regression test. Use when something is broken, throwing, failing tests, or behaving unexpectedly.
model_invocable: true
---
# Debug Issue

Fix root causes, not symptoms. Let evidence drive the fix.

## Workflow
```
- [ ] 1. Reproduce the failure reliably
- [ ] 2. Gather evidence (error, stack trace, logs, failing test)
- [ ] 3. Form a hypothesis about the root cause
- [ ] 4. Isolate (minimal repro, bisect, add temporary logging)
- [ ] 5. Confirm the root cause with evidence — don't guess-fix
- [ ] 6. Apply the smallest correct fix
- [ ] 7. Add a regression test that fails before, passes after
- [ ] 8. Run the suite (run-tests) and clean up temporary logging
```

## Rules
- State your hypothesis and the evidence that confirms it before editing code.
- Prefer a minimal reproduction over reasoning about the whole system.
- If the fix reveals a design issue, note it (consider `record-decision`).
