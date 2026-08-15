"""Backend selection and degradation.

Degradation is silent **by default**: if the preferred backend disappears, the
next one engages and ordinary command output is unchanged. That is the product
promise — a developer should never be handed a problem they did not ask about.

It is not, however, hidden. ``ckeel doctor``, ``ckeel internals`` and expert
mode all report which backend was chosen, which was skipped, and exactly why.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from contextkeel.errors import BackendUnavailable
from contextkeel.graph.base import GraphBackend, IndexResult
from contextkeel.graph.fallback_backend import FallbackBackend
from contextkeel.graph.graphify_backend import GraphifyBackend
from contextkeel.state import State

log = logging.getLogger("contextkeel")


def all_backends(*, allow_install: bool = True) -> list[GraphBackend]:
    """Highest priority first."""
    backends: list[GraphBackend] = [
        GraphifyBackend(allow_install=allow_install),
        FallbackBackend(),
    ]
    return sorted(backends, key=lambda b: b.priority, reverse=True)


@dataclass
class Selection:
    backend: GraphBackend
    degraded: bool = False
    reason: str = ""
    skipped: list[tuple[str, str]] = None  # (name, why)

    def __post_init__(self) -> None:
        if self.skipped is None:
            self.skipped = []


def select(
    state: State,
    *,
    override: str = "",
    pinned: str = "",
    allow_install: bool = True,
    refresh: bool = False,
) -> Selection:
    """Choose a backend.

    Precedence: explicit ``--backend`` flag, then ``context.backend`` pinned in
    project.yml, then the cached choice, then a fresh probe by priority.
    """
    backends = all_backends(allow_install=allow_install)
    by_name = {b.name: b for b in backends}
    preferred = backends[0].name

    wanted = (override or pinned).strip()
    if wanted:
        backend = by_name.get(wanted)
        if backend is None:
            known = ", ".join(sorted(by_name))
            raise BackendUnavailable(
                f"unknown backend {wanted!r}; available: {known}", backend=wanted
            )
        # An explicit choice is obeyed even if probing says otherwise: an
        # expert who asks for something specific gets it, or a real error.
        return Selection(
            backend=backend,
            degraded=backend.name != preferred,
            reason=f"selected explicitly ({'flag' if override else 'project.yml'})",
        )

    if not refresh and state.selected_backend in by_name:
        backend = by_name[state.selected_backend]
        return Selection(
            backend=backend,
            degraded=state.backend_degraded,
            reason=state.backend_reason or "cached selection",
        )

    skipped: list[tuple[str, str]] = []
    for backend in backends:
        try:
            available = backend.is_available()
        except Exception as exc:  # noqa: BLE001 - a probe must never crash selection
            skipped.append((backend.name, f"probe raised: {exc}"))
            continue
        if available:
            degraded = backend.name != preferred
            reason = (
                f"preferred backend unavailable ({skipped[0][1]})"
                if degraded and skipped
                else "available"
            )
            return Selection(
                backend=backend, degraded=degraded, reason=reason, skipped=skipped
            )
        skipped.append((backend.name, "not available on this machine"))

    # FallbackBackend.is_available() is unconditionally True, so this is
    # unreachable in practice — but never leave the caller without an index.
    return Selection(
        backend=FallbackBackend(),
        degraded=True,
        reason="no backend probed successfully",
        skipped=skipped,
    )


def remember(state: State, selection: Selection) -> None:
    """Persist the choice so the probe is not repeated on every command."""
    state.selected_backend = selection.backend.name
    state.backend_degraded = selection.degraded
    state.backend_reason = selection.reason
    version = getattr(selection.backend, "version", "")
    state.backend_probed_version = version if isinstance(version, str) else ""


def build_index(
    selection: Selection, root: Path, *, incremental: bool = True
) -> IndexResult:
    """Build or update, degrading to the fallback if the chosen backend fails.

    A backend that passes its probe can still fail at run time; when that
    happens mid-command the user should still end up with an index.
    """
    backend = selection.backend
    try:
        return backend.update(root) if incremental else backend.build(root)
    except BackendUnavailable as exc:
        if isinstance(backend, FallbackBackend):
            raise
        log.warning("backend %s failed at run time: %s", backend.name, exc.detail)
        selection.degraded = True
        selection.reason = f"runtime failure: {exc.detail[:200]}"
        selection.backend = FallbackBackend()
        return selection.backend.build(root)


__all__ = ["Selection", "all_backends", "build_index", "remember", "select"]
