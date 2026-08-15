"""MCP server (stdio).

Registered automatically by the render step, so every editor gets these tools
from a single ``ckeel init`` with no manual configuration.

**stdout is the protocol channel.** A stray ``print`` anywhere in the call path
corrupts the stream and takes the server down — it is the most common way to
break an MCP server — so every message goes through the file logger instead,
and the console is forced quiet before the transport starts.

Startup is non-blocking: a missing index is built lazily on first use rather
than delaying the handshake.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from contextkeel.mcp.tools import HANDLERS, TOOL_SCHEMAS

log = logging.getLogger("contextkeel.mcp")


def _silence_console() -> None:
    """Nothing but protocol frames may reach stdout."""
    from contextkeel import console

    console.configure(quiet=True)


def serve(root: Path | None = None) -> int:
    try:
        import anyio
        import mcp.types as types
        from mcp.server.lowlevel.server import Server
        from mcp.server.stdio import stdio_server
    except ImportError:
        print(
            "The MCP server needs the 'mcp' extra: uv tool install 'contextkeel[mcp]'",
            file=sys.stderr,
        )
        return 1

    from contextkeel import paths
    from contextkeel.__about__ import __version__

    resolved_root = paths.find_repo_root(root)
    _silence_console()
    log.info("mcp server starting for %s", resolved_root)

    async def on_list_tools(ctx, params) -> types.ListToolsResult:  # noqa: ANN001
        return types.ListToolsResult(
            tools=[
                types.Tool(
                    name=schema["name"],
                    description=schema["description"],
                    inputSchema=schema["inputSchema"],
                )
                for schema in TOOL_SCHEMAS
            ]
        )

    async def on_call_tool(ctx, params) -> types.CallToolResult:  # noqa: ANN001
        def result(text: str, *, error: bool = False) -> types.CallToolResult:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=text)], isError=error
            )

        handler = HANDLERS.get(params.name)
        if handler is None:
            return result(f"Unknown tool: {params.name}", error=True)
        try:
            # Structured tool errors, never a crashed server.
            return result(str(handler(resolved_root, **(params.arguments or {}))))
        except TypeError as exc:
            log.warning("bad arguments for %s: %s", params.name, exc)
            return result(f"Invalid arguments for {params.name}: {exc}", error=True)
        except Exception as exc:  # noqa: BLE001 - the server must survive
            log.exception("tool %s failed", params.name)
            return result(f"{params.name} failed: {exc}", error=True)

    server = Server(
        "contextkeel",
        version=__version__,
        instructions=(
            "Call load_context once at the start of a task instead of reading "
            "many files, and query_index instead of globbing the repository."
        ),
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
    )

    async def _run() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )

    try:
        anyio.run(_run)
    except KeyboardInterrupt:
        return 0
    except Exception:  # noqa: BLE001
        log.exception("mcp server crashed")
        return 1
    return 0


__all__ = ["serve"]
