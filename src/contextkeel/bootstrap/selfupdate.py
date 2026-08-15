"""Self-upgrade and state migration."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

from contextkeel import platform as ckplat
from contextkeel.__about__ import __version__
from contextkeel.state import SCHEMA_VERSION, State

log = logging.getLogger("contextkeel")

CHECK_INTERVAL_SECONDS = 24 * 60 * 60


@dataclass(frozen=True)
class UpgradeResult:
    ok: bool
    detail: str
    from_version: str = ""
    to_version: str = ""


def upgrade(*, dry_run: bool = False) -> UpgradeResult:
    """Upgrade the installed tool in place.

    Callers are expected to re-render the agent configs afterwards, so an
    upgraded package refreshes the files it previously generated.
    """
    uv = ckplat.which("uv")
    if not uv:
        return UpgradeResult(False, "uv is not available; re-run the installer")

    if dry_run:
        result = ckplat.run([str(uv), "tool", "list"], timeout=60)
        return UpgradeResult(
            True, f"would upgrade contextkeel (currently {__version__})\n{result.out}"
        )

    result = ckplat.run([str(uv), "tool", "upgrade", "contextkeel"], timeout=600)
    if not result.ok:
        return UpgradeResult(False, result.output[:400], from_version=__version__)
    return UpgradeResult(
        True, result.output.strip() or "upgraded", from_version=__version__
    )


# --------------------------------------------------------------------------
# State migration
# --------------------------------------------------------------------------

#: schema_version -> function upgrading a raw dict to the next version.
_MIGRATIONS: dict[int, callable] = {}


def register_migration(from_version: int):
    def decorator(fn):
        _MIGRATIONS[from_version] = fn
        return fn

    return decorator


def migrate_state(state: State, state_path: Path) -> State:
    """Step a state file forward to the current schema. Never destructive."""
    if state.schema_version >= SCHEMA_VERSION:
        return state

    if state_path.is_file():
        backup = state_path.with_suffix(f".json.v{state.schema_version}.bak")
        try:
            backup.write_text(state_path.read_text(encoding="utf-8"), encoding="utf-8")
        except OSError:
            log.warning("could not back up state before migration")

    from dataclasses import asdict

    raw = asdict(state)
    version = state.schema_version
    while version < SCHEMA_VERSION:
        migration = _MIGRATIONS.get(version)
        if migration is None:
            break
        raw = migration(raw)
        version += 1
        raw["schema_version"] = version

    known = set(State().__dataclass_fields__)
    return State(**{k: v for k, v in raw.items() if k in known})


# --------------------------------------------------------------------------
# Update check — best effort, cached, never blocks a command
# --------------------------------------------------------------------------


def check_for_update(cache_file: Path) -> str | None:
    """Return a newer version string, or None. Silent on any failure."""
    try:
        if cache_file.is_file():
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if time.time() - cached.get("checked_at", 0) < CHECK_INTERVAL_SECONDS:
                latest = cached.get("latest")
                return latest if latest and latest != __version__ else None
    except Exception:  # noqa: BLE001 - a cache read must never break a command
        pass

    try:
        import urllib.request

        with urllib.request.urlopen(  # noqa: S310 - fixed https URL
            "https://pypi.org/pypi/contextkeel/json", timeout=3
        ) as response:
            latest = json.load(response)["info"]["version"]
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(
            json.dumps({"checked_at": time.time(), "latest": latest}), encoding="utf-8"
        )
        return latest if latest != __version__ else None
    except Exception:  # noqa: BLE001 - offline is normal, not an error
        return None


__all__ = [
    "UpgradeResult",
    "check_for_update",
    "migrate_state",
    "register_migration",
    "upgrade",
]
