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
    """Build the server list with every path resolved against ``root``."""
    root = root.resolve()
    vault_dir = vault_dir.resolve()

    return [
        # This package's own server: one entry point gives every editor the
        # same context tools with no manual configuration.
        McpServerDef(
            name="contextkeel",
            command="ckeel",
            args=["mcp-serve", "--root", _path(root)],
        ),
        McpServerDef(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", _path(vault_dir)],
        ),
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
