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

## What you need

**Nothing.** The installer fetches everything, in this order:

1. **uv** — a single standalone binary, downloaded by the install line.
2. **Python 3.11+** — supplied *by* uv, so your system Python is irrelevant and
   no package manager or `sudo` is involved.
3. **contextkeel** — installed by uv as an isolated tool.
4. **The code indexer** — installed automatically the first time it is needed.

The only thing that must already exist is `curl` or `wget` on macOS/Linux, and
PowerShell on Windows. Both are present on a stock system.

### Optional extras

None of these block anything. contextkeel checks for each and adapts.

| Thing | What it adds | If missing |
|---|---|---|
| **Node / npx** | One extra MCP server that reads your notes folder | That server is simply left out of the generated config. Everything else works. Install from [nodejs.org](https://nodejs.org) if you want it. |
| **Obsidian** | A nice reader for your project notes | Notes are plain Markdown and open in any editor. Install from [obsidian.md](https://obsidian.md), or run `ckeel init --with-viewer` to retry the automatic install. |
| **An LLM API key** | Documentation summarised in the code index | Code is still indexed in full. See *How the code index is built* below. |

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

## Reviewing a project

Picking up someone else's repository, or checking a junior's work? After
`ckeel sync` there are three things to open, in increasing detail:

| Open | To see |
|---|---|
| `Vault/Changelog.md` | What shipped, newest first, in plain sentences. |
| `graphify-out/graph.html` | The codebase as an interactive graph, in a browser. |
| `Vault/` in [Obsidian](https://obsidian.md) | Conventions, glossary, API contracts, and the decision log, cross-linked. |

`ckeel status` prints where these live. Obsidian is optional — the vault is
plain Markdown, so any editor works — and the graph is a self-contained HTML
file needing no server.

One thing to know: `graphify-out/` and `.contextkeel/` are generated and
git-ignored, so a fresh clone will not have them. Run `ckeel sync` once and
they appear. `Vault/` **is** committed, so the notes travel with the repo.

## Under the hood

Everything above is the short version. Nothing is hidden — run
**`ckeel internals`** and it prints exactly what is running: the real name and
version of the code indexer it chose, why it chose that one, the precise
commands it runs on your behalf, and every setting with its current value and
where that value came from.

### How the code index is built

The index comes from [graphify](https://github.com/safishamsi/graphify), and it
runs in one of three modes. **You do not have to choose one** — contextkeel
picks the best available and tells you which if you ask.

| Mode | When | What you get |
|---|---|---|
| **code-only** *(default)* | no API key set | Your code, parsed locally. No key, no network, no cost. |
| **full** | any supported API key is set | The above, plus your docs summarised by an LLM. |
| **claude-cli** | you opt in, and Claude Code is installed | Same as full, billed to your Claude subscription instead of an API key. |

**Most people want the default and need to do nothing.** contextkeel indexes
code for navigation, and code needs no AI to parse. An LLM only adds summaries
of your `.md` files — pleasant, not necessary.

To get the richer mode, either export a key —
`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`,
`MOONSHOT_API_KEY` or `DEEPSEEK_API_KEY` — or, if you already use Claude Code,
set `context.use_claude_cli: true` in `project.yml` to reuse that subscription.
It is off by default because it spends your Claude quota on every index build,
which is not a cost to incur without being asked.

Should graphify be unusable for any reason, a tree-sitter indexer bundled with
the package takes over. It works entirely offline. The changeover is silent by
design — your output is identical — and `ckeel doctor` says which is in use.

Project notes are plain Markdown. If [Obsidian](https://obsidian.md) is
installed they open nicely in it, but it is only a viewer and is never
required.

Useful overrides, all documented in `--help`:

| Flag | Effect |
|---|---|
| `--backend <name>` | Pick a specific code indexer (also pinnable via `context.backend` in `project.yml`). |
| `context.use_claude_cli` | Index via your Claude Code subscription instead of an API key. |
| `--with-viewer` / `--no-viewer` | Force or skip the notes-viewer install. |
| `--expert` | Name every underlying tool in normal output. Also `CONTEXTKEEL_EXPERT=1`. |
| `ckeel index -- <args>` | Pass arguments straight through to the indexer. |

See [docs/internals.md](docs/internals.md) for the full picture.

## Licence

MIT — see [LICENSE](LICENSE).
