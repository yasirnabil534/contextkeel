"""Hook definitions, as data.

Commands are always ``ckeel _hook <name>`` — a shim on PATH that behaves
identically on macOS, Windows and Linux. The original template invoked
``node .cursor/hooks/tidy-markdown.js``, which breaks the moment Node is
absent or the repository moves; an installed console script cannot.
"""

from __future__ import annotations

from contextkeel.render.model import HookDef

TIDY = "tidy"
SYNC = "sync"
SYNC_ON_STOP = "sync-on-stop"


def default_hooks() -> list[HookDef]:
    """The hooks this tool owns.

    ``sync-on-stop`` is the mechanism behind the product's core promise: the
    context refreshes when a session ends, so nothing depends on an agent
    remembering to do it.
    """
    return [
        HookDef(
            event="PostToolUse",
            matcher="Write|Edit|MultiEdit",
            command=["ckeel", "_hook", TIDY],
        ),
        HookDef(
            event="PostToolUse",
            matcher="Write|Edit|MultiEdit",
            command=["ckeel", "_hook", SYNC],
        ),
        HookDef(
            event="Stop",
            matcher="*",
            command=["ckeel", "_hook", SYNC_ON_STOP],
        ),
    ]


__all__ = ["SYNC", "SYNC_ON_STOP", "TIDY", "default_hooks"]
