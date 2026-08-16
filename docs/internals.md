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
| `graphify` | 100 | External CLI. Richer graph: real call edges, communities. |
| `builtin` | 10 | Ships in the package. tree-sitter parse, offline, no key. Degrades again to a regex scan if tree-sitter cannot load. |

### graphify runs in one of three modes

An LLM is needed **only to summarise documentation files**, which this tool
does not use — we want a code map for navigation. So a missing API key selects
a cheaper mode rather than disqualifying the backend:

| Mode | Selected when | Command |
|---|---|---|
| `full` | any key in `API_KEY_VARS` is set | `graphify .` |
| `claude-cli` | `context.use_claude_cli: true` **and** the `claude` binary exists | `graphify . --backend claude-cli` |
| `code-only` | otherwise (the default) | `graphify . --code-only` |

`claude-cli` drives the Claude Code binary, which authenticates by
subscription rather than an API key. It is opt-in because every index build
consumes that quota. Note a Claude subscription and a `console.anthropic.com`
API key are separate things; graphify supports both.

An earlier version of this tool treated "no API key" as "graphify is
unusable" and always fell back to the bundled indexer. That was wrong, and it
meant nearly every user silently got the weaker index.

### Selection

Order: `--backend` flag, then `context.backend` in `project.yml`, then the
cached choice, then a fresh probe by priority.

A backend that passes its probe can still fail at run time; when that happens
the fallback takes over for that run only. The **probed** choice is what gets
cached, never the runtime substitution — otherwise one transient failure would
downgrade the user permanently and silently, with no way back.

Because a cached selection skips `is_available()`, the flag probe is also run
lazily before building. Without that, `supports()` answers False for every
flag and the code-only path never engages after the first run.

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

## MCP servers

Three, and none of them needs a runtime the installer does not provide:

| Server | Runs via |
|---|---|
| `contextkeel` | this package's own CLI |
| `git`, `fetch` | `uvx`, which ships with uv |

A Node-based filesystem server used to sit here, pointed at the notes folder.
It was inherited from the template contextkeel replaced and never questioned.
The notes folder is always inside the repository, so that server duplicated
file access the editor already has natively — while making a JavaScript
runtime a de-facto requirement. It was removed, and `read_note`/`write_note`
on our own server cover the same ground for clients that lack file tools.

Note paths from those tools are resolved and then checked for containment in
the notes folder. Checking the string for `..` is not equivalent: symlinks and
absolute paths bypass it, and the path comes from a model, so traversal is a
realistic input rather than a hypothetical one.
