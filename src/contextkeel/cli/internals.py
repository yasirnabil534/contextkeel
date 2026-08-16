"""``ckeel internals`` — full disclosure.

The neutral default register is a courtesy, not a wall. This command names
every underlying tool, prints the exact commands run on the developer's
behalf, and shows where each effective setting came from.
"""

from __future__ import annotations

from pathlib import Path

from contextkeel import console, expert
from contextkeel.cli.common import open_workspace


def run(root: Path | None = None, *, json_mode: bool = False) -> int:
    workspace = open_workspace(root)
    data = expert.collect(workspace.root, workspace.config, workspace.state)

    if json_mode:
        console.emit_json(data)
        return 0

    # This command is always the expert register — that is its whole purpose.
    console.configure(expert=True)

    _section("contextkeel", data["contextkeel"])
    _section("workspace", data["workspace"])

    backend = data["index_backend"]
    print("\nindex backend")
    print(f"  selected        : {backend['selected']}")
    print(f"  mode            : {backend['mode']}")
    print(f"  why             : {backend['why_this_mode']}")
    print(f"  API key set     : {backend['api_key_set']}")
    print(f"  claude CLI      : {backend['claude_cli_installed']}")
    print(f"  degraded        : {backend['degraded']}")
    print(f"  reason          : {backend['reason'] or '—'}")
    for candidate in backend["candidates"]:
        print(
            f"  · {candidate['name']:<10} priority={candidate['priority']:<4} "
            f"available={candidate['available']} "
            f"version={candidate['version'] or '—'}"
        )

    print("\ncommands run on your behalf")
    for label, command in data["commands_run_on_your_behalf"].items():
        print(f"  {label:<28} {command}")

    _section("notes viewer", data["notes_viewer"])

    print("\noverrides")
    for flag, origin in data["overrides"].items():
        print(f"  {flag:<28} {origin['value']}  (from: {origin['source']})")

    vocab = data["vocabulary"]
    print(f"\nvocabulary — {vocab['note']}")
    for internal, neutral in sorted(vocab["mapping"].items()):
        print(f"  {internal:<28} → {neutral}")

    return 0


def _section(title: str, values: dict) -> None:
    print(f"\n{title}")
    for key, value in values.items():
        if isinstance(value, dict):
            value = ", ".join(f"{k}={v}" for k, v in value.items())
        print(f"  {key:<16}: {value}")


def index_passthrough(root: Path | None, args: list[str]) -> int:
    """``ckeel index -- <args>`` — hand the real indexer straight through."""
    return expert.passthrough(Path(root) if root else Path.cwd(), args)


__all__ = ["index_passthrough", "run"]
