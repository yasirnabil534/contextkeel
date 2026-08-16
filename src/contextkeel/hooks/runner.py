"""The ``ckeel _hook <name>`` entry point.

This runs on every file edit in every agent session, so its failure modes
matter far more than its features. The governing rule:

    **It always exits 0 and always writes valid JSON to stdout.**

A hook that breaks a developer's edit loop is a catastrophic failure of the
product promise. A hook that silently does nothing is a missed optimisation.
Those are not close, so every exception is caught, logged to file, and
swallowed.

Work is also debounced: a burst of twenty writes must trigger one index
update, not twenty.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
from pathlib import Path

log = logging.getLogger("contextkeel")

WALL_CLOCK_TIMEOUT = 5.0
DEBOUNCE_SECONDS = 45.0

_ENVELOPE = "{}"


def _file_path_from(payload: dict) -> Path | None:
    """Tolerate both payload shapes.

    Claude Code nests tool arguments under ``tool_input``; Cursor passes them
    flat. Support both rather than assuming one.
    """
    nested = payload.get("tool_input") or {}
    candidates = [
        payload.get("file_path"),
        payload.get("filePath"),
        payload.get("path"),
        nested.get("file_path"),
        nested.get("path"),
        (payload.get("file") or {}).get("path")
        if isinstance(payload.get("file"), dict)
        else None,
    ]
    for candidate in candidates:
        if candidate:
            return Path(str(candidate))
    return None


def tidy_markdown(payload: dict) -> None:
    """Normalise whitespace in a markdown file that was just written."""
    path = _file_path_from(payload)
    if path is None or path.suffix.lower() != ".md" or not path.is_file():
        return
    original = path.read_text(encoding="utf-8", errors="replace")
    tidied = "\n".join(line.rstrip() for line in original.split("\n"))
    while "\n\n\n" in tidied:
        tidied = tidied.replace("\n\n\n", "\n\n")
    tidied = tidied.rstrip("\n") + "\n"
    if tidied != original:
        path.write_text(tidied, encoding="utf-8")


def sync_index(payload: dict, *, force: bool = False) -> None:
    """Refresh the index, debounced against recent runs."""
    from contextkeel import paths
    from contextkeel import state as state_mod
    from contextkeel.config import load as load_config
    from contextkeel.config import resolve
    from contextkeel.graph import registry, report

    path = _file_path_from(payload)
    layout = paths.layout(path.parent if path else None)
    layout.ensure()

    current = state_mod.load(layout.state_file)
    if not force and current.seconds_since_hook() < DEBOUNCE_SECONDS:
        log.debug("hook debounced (%.1fs since last run)", current.seconds_since_hook())
        return

    cfg = resolve(load_config(layout.root), layout.root)
    selection = registry.select(
        current,
        pinned=cfg.context.backend,
        allow_install=False,
        use_claude_cli=cfg.context.use_claude_cli,
    )
    result = registry.build_index(selection, layout.root, incremental=True)
    report.write(result, layout.index)

    registry.remember(current, selection)
    current.touch_hook()
    current.touch_sync()
    state_mod.save(current, layout.state_file)


HANDLERS = {
    "tidy": tidy_markdown,
    "sync": sync_index,
    "sync-on-stop": lambda payload: sync_index(payload, force=True),
}


def _read_stdin() -> dict:
    try:
        if sys.stdin is None or sys.stdin.closed:
            return {}
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:  # noqa: BLE001 - a malformed payload is not our problem
        return {}


def run(name: str) -> int:
    """Execute a hook. Returns 0 unconditionally."""
    try:
        payload = _read_stdin()
        handler = HANDLERS.get(name)
        if handler is None:
            log.debug("unknown hook %r", name)
        else:
            # Hard wall clock: exceeding it abandons the work, not the edit.
            done = threading.Event()
            error: list[BaseException] = []

            def _target() -> None:
                try:
                    handler(payload)
                except BaseException as exc:  # noqa: BLE001 - fail open
                    error.append(exc)
                finally:
                    done.set()

            worker = threading.Thread(target=_target, daemon=True)
            worker.start()
            if not done.wait(WALL_CLOCK_TIMEOUT):
                log.warning(
                    "hook %s exceeded %.1fs; abandoning", name, WALL_CLOCK_TIMEOUT
                )
            elif error:
                log.warning("hook %s failed: %s", name, error[0], exc_info=error[0])
    except BaseException as exc:  # noqa: BLE001 - nothing may escape
        log.warning("hook %s crashed: %s", name, exc, exc_info=exc)

    # stdout carries the protocol envelope and nothing else.
    sys.stdout.write(_ENVELOPE)
    sys.stdout.flush()
    return 0


__all__ = ["DEBOUNCE_SECONDS", "HANDLERS", "WALL_CLOCK_TIMEOUT", "run"]
