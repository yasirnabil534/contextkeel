"""MCP server configuration.

This module exists because of a specific, real failure: three checked-in MCP
config files hardcoding one developer's ``D:\\Learnings\\Template`` path, which
was broken on every other machine and silently disabled the whole MCP layer.

The fix is structural rather than careful. Paths are resolved *at render time*
from the repository root — never from a literal, never from a value captured
when the package was built — and one function produces the dictionary that all
three editors serialise, so the three files cannot disagree. Re-rendering on
every ``init``/``sync`` means moving or renaming the repo self-heals.
"""

from __future__ import annotations

from pathlib import Path

from contextkeel.render.model import McpServerDef


def servers_for(root: Path, vault_dir: Path) -> list[McpServerDef]:
    """Build the server list with every path resolved against ``root``.

    Every server here runs on something the installer guarantees: this
    package's own CLI, or uvx which ships with uv. Nothing needs Node.
    """
    root = root.resolve()
    _ = vault_dir  # served by our own server now, not a separate one

    return [
        # This package's own server: one entry point gives every editor the
        # same context tools with no manual configuration. It also serves the
        # notes, which is why no Node-based filesystem server is needed --
        # that one duplicated file access the editor already has, and dragged
        # a whole extra runtime behind it.
        McpServerDef(
            name="contextkeel",
            command="ckeel",
            args=["mcp-serve", "--root", _path(root)],
        ),
        # uvx ships with uv, which the installer guarantees.
        McpServerDef(
            name="git",
            command="uvx",
            args=["mcp-server-git", "--repository", _path(root)],
        ),
        McpServerDef(name="fetch", command="uvx", args=["mcp-server-fetch"]),
    ]


def _path(path: Path) -> str:
    """Serialise a path for JSON.

    The single place a :class:`Path` becomes a string. Call sites must not use
    ``str()`` directly — routing every conversion through here is what keeps
    separator handling consistent, and what makes the "no foreign absolute
    path" test meaningful.
    """
    return str(path)


def to_dict(servers: list[McpServerDef]) -> dict:
    """The payload every target serialises. Identical across all three."""
    return {
        "mcpServers": {
            server.name: {
                "command": server.command,
                "args": list(server.args),
                **({"env": dict(server.env)} if server.env else {}),
            }
            for server in servers
        }
    }


def build(root: Path, vault_dir: Path) -> dict:
    return to_dict(servers_for(root, vault_dir))


__all__ = ["build", "servers_for", "to_dict"]
