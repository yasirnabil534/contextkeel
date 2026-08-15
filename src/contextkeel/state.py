"""Durable workspace state (``.contextkeel/state.json``).

Written atomically so a crash mid-write cannot corrupt it, and tolerant on
read so a corrupt file degrades to defaults instead of breaking every command.
The one case that *is* an error is a state file from a newer schema than this
build understands — silently mangling that would be worse than stopping.
"""

from __future__ import annotations

import contextlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from contextkeel.errors import StateError

log = logging.getLogger("contextkeel")

SCHEMA_VERSION = 1


@dataclass
class State:
    schema_version: int = SCHEMA_VERSION
    contextkeel_version: str = ""
    selected_backend: str = ""
    backend_degraded: bool = False
    backend_reason: str = ""
    backend_probed_version: str = ""
    last_sync: str = ""
    last_sync_sha: str = ""
    last_hook_run: str = ""
    viewer_installed: str = "not-attempted"  # yes | no | not-attempted
    rendered_fingerprints: dict[str, str] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)

    def touch_sync(self, sha: str = "") -> None:
        self.last_sync = datetime.now(UTC).isoformat(timespec="seconds")
        self.last_sync_sha = sha

    def touch_hook(self) -> None:
        self.last_hook_run = datetime.now(UTC).isoformat(timespec="seconds")

    def seconds_since_hook(self) -> float:
        if not self.last_hook_run:
            return float("inf")
        try:
            then = datetime.fromisoformat(self.last_hook_run)
        except ValueError:
            return float("inf")
        return (datetime.now(UTC) - then).total_seconds()


def load(path: Path) -> State:
    """Read state, tolerating absence and corruption."""
    if not path.is_file():
        return State()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("state.json unreadable (%s); backing up and resetting", exc)
        _backup(path)
        return State()

    version = raw.get("schema_version", 0)
    if version > SCHEMA_VERSION:
        raise StateError(
            f"state schema {version} is newer than supported {SCHEMA_VERSION}"
        )

    known = {f for f in State().__dataclass_fields__}
    return State(**{k: v for k, v in raw.items() if k in known})


def save(state: State, path: Path) -> None:
    """Atomic write: temp file in the same directory, then replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    state.schema_version = SCHEMA_VERSION
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(asdict(state), indent=2, sort_keys=True), encoding="utf-8"
    )
    tmp.replace(path)


def _backup(path: Path) -> None:
    with contextlib.suppress(OSError):
        path.replace(path.with_suffix(".json.bak"))


__all__ = ["SCHEMA_VERSION", "State", "load", "save"]
