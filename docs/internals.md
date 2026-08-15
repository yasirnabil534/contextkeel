# Internals

Written for the curious and for contributors. Nothing here is required to use
contextkeel — `ckeel internals` prints most of it for your actual machine.

## The two output registers

The default register rewrites internal tool names to neutral equivalents
("code index", "notes viewer"). The expert register leaves text untouched.

Expert mode turns on with `--expert`, `--verbose`, `--json`, or
`CONTEXTKEEL_EXPERT=1`. `--json` is *always* expert: a script that had to parse
"code index" instead of the real backend id would be broken by design.

This is a default, not a restriction. Everything the tool knows is reachable,
and `ckeel internals` prints the neutral-to-real mapping so any message you have
seen can be translated back.

## Index backends

| Backend | Priority | Notes |
|---|---|---|
| `graphify` | 100 | External CLI. Richer graph. **Needs an LLM API key** whenever the repository contains documentation files — which, after `ckeel init`, it always does. |
| `builtin` | 10 | Ships in the package. tree-sitter parse, offline, no key. Degrades again to a regex scan if tree-sitter cannot load. |

Selection order: `--backend` flag, then `context.backend` in `project.yml`, then
the cached choice, then a fresh probe by priority. A backend that passes its
probe but fails at run time is caught mid-command and the fallback takes over,
so you always end up with an index.

Because `graphify` aborts without an API key, most machines will quietly use
the built-in indexer. That is the intended behaviour, not a fault — set
`ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`,
`MOONSHOT_API_KEY`) if you want the richer one.

## Generated files

Everything under `.claude/`, `.cursor/`, `.continue/`, plus `AGENTS.md` and
`.mcp.json`, is rendered from one canonical source inside the package
(`render/content/`). A skill's description and its invocation flag exist in
exactly one place, which is what makes the three editors incapable of drifting
apart.

Writes are atomic and fingerprinted. If you hand-edit a generated file, the
next render notices, leaves your version alone, and reports it through
`ckeel doctor`. Move the change into the source if you want it to stick.

`.claude/settings.json` and `.cursor/hooks.json` are *merged* rather than
replaced, so permissions and hooks you add yourself survive.

## Hooks

Hooks run as `ckeel _hook <name>` — an installed console script, which works
identically on all three platforms and survives the repository being moved.

The runner always exits 0 and always writes `{}` to stdout, whatever happens.
A hook that breaks an edit loop is a catastrophic failure; a hook that silently
does nothing is a missed optimisation. Work is debounced, so a burst of writes
triggers one index update.

## Paths

Every generated path is resolved from the repository root at render time.
Moving or renaming the repo and running `ckeel sync` rewrites them all.
