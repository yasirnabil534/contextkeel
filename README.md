# contextkeel

**macOS / Linux**

```sh
curl -LsSf https://contextkeel.dev/install.sh | sh
```

**Windows (PowerShell)**

```powershell
irm https://contextkeel.dev/install.ps1 | iex
```

That is the whole setup. Nothing needs to be installed first — not even Python.

---

## What happens after that

Run it in a repository and it works out what the project is, writes the
configuration your editor needs, and builds an index of the codebase so your AI
assistant can find things without reading half the repo first. From then on it
keeps itself current in the background.

You do not have to learn a workflow, maintain any notes, or think about
context again.

## Commands

| Command | What it does |
|---|---|
| `ckeel init` | Set a repository up. Safe to run again at any time. |
| `ckeel doctor` | Check everything, and `--fix` to repair it. |
| `ckeel sync` | Refresh the index and notes. Usually automatic. |
| `ckeel status` | Where the project stands, in five lines. |
| `ckeel plan` | Turn requirements into a trackable prompt plan. |

## Editors

Claude Code, Cursor and Continue are configured automatically — all three from
the same source, so they behave identically and cannot drift apart. No manual
setup, no config files to copy, no paths to fix by hand.

Any other MCP-capable editor can use the bundled server directly.

## Under the hood

Everything above is the short version. Nothing is hidden — run
**`ckeel internals`** and it prints exactly what is running: the real name and
version of the code indexer it chose, why it chose that one, the precise
commands it runs on your behalf, and every setting with its current value and
where that value came from.

The code index normally comes from [graphify](https://github.com/safishamsi/graphify);
when that is unavailable — including when it has no LLM API key, which it needs
for repositories containing documentation — contextkeel falls back to a
built-in tree-sitter indexer that ships with the package and works offline.
The changeover is deliberate and silent: your output is identical either way,
and `ckeel doctor` will tell you which one is in use.

Project notes are plain Markdown. If [Obsidian](https://obsidian.md) is
installed they open nicely in it, but it is only a viewer and is never
required.

Useful overrides, all documented in `--help`:

| Flag | Effect |
|---|---|
| `--backend <name>` | Pick a specific code indexer (also pinnable via `context.backend` in `project.yml`). |
| `--with-viewer` / `--no-viewer` | Force or skip the notes-viewer install. |
| `--expert` | Name every underlying tool in normal output. Also `CONTEXTKEEL_EXPERT=1`. |
| `ckeel index -- <args>` | Pass arguments straight through to the indexer. |

See [docs/internals.md](docs/internals.md) for the full picture.

## Licence

MIT — see [LICENSE](LICENSE).
