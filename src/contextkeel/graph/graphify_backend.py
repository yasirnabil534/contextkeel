"""Adapter for the preferred third-party indexer.

This is the only file in the package that knows this tool exists. Its native
output never leaks past the parsing step: everything crossing the boundary is
the neutral schema from :mod:`contextkeel.graph.base`.

Every failure mode raises :class:`BackendUnavailable`, which the registry
turns into a silent downgrade. The developer sees nothing; ``ckeel internals``
sees everything.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from contextkeel import platform as ckplat
from contextkeel.errors import BackendUnavailable
from contextkeel.graph.base import (
    Community,
    Edge,
    EdgeKind,
    IndexResult,
    Node,
    NodeKind,
)

log = logging.getLogger("contextkeel")

CLI = "graphify"
PACKAGE = "graphifyy"
BUILD_TIMEOUT = 900
PROBE_TIMEOUT = 30

#: This backend performs semantic extraction on documentation files and aborts
#: with "no LLM API key found" when it cannot. Any repository this tool has set
#: up contains dozens of generated markdown files, so without one of these keys
#: the backend fails on essentially every real project. Detect that up front
#: rather than discovering it mid-build: the failure is predictable, so the
#: degradation should be too.
API_KEY_VARS = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "MOONSHOT_API_KEY",
)


class GraphifyBackend:
    """Wraps the external indexer CLI."""

    name = "graphify"
    priority = 100

    def __init__(self, *, allow_install: bool = True) -> None:
        self._allow_install = allow_install
        self._version: str | None = None
        self._flags: set[str] | None = None
        self._install_attempted = False

    # -- availability -------------------------------------------------------

    def is_available(self) -> bool:
        if not has_api_key():
            # Would fail during the build anyway; skipping here also avoids a
            # pointless install and stops it leaving output behind.
            log.debug("no LLM API key set; %s cannot index doc-bearing repos", CLI)
            return False
        if ckplat.which(CLI):
            return self._probe()
        if self._allow_install and not self._install_attempted:
            self._install_attempted = True
            if self._install():
                return self._probe()
        return False

    def _install(self) -> bool:
        """One quiet attempt, never retried in a loop."""
        uv = ckplat.which("uv")
        if not uv:
            return False
        log.debug("attempting %s install via uv", PACKAGE)
        result = ckplat.run([str(uv), "tool", "install", PACKAGE], timeout=600)
        if not result.ok:
            log.debug("%s install failed: %s", PACKAGE, result.output[:300])
            return False
        ckplat.ensure_on_path(ckplat.user_bin_dir())
        return ckplat.which(CLI) is not None

    def _probe(self) -> bool:
        """Cache version and supported flags; never assume they are stable."""
        if self._version is not None:
            return True
        cli = ckplat.which(CLI)
        if not cli:
            return False
        version = ckplat.run([str(cli), "--version"], timeout=PROBE_TIMEOUT)
        if not version.ok:
            return False
        self._version = version.output.strip()

        help_text = ckplat.run([str(cli), "--help"], timeout=PROBE_TIMEOUT)
        self._flags = {
            token for token in help_text.output.split() if token.startswith("--")
        }
        log.debug("%s %s flags=%s", CLI, self._version, sorted(self._flags))
        return True

    @property
    def version(self) -> str:
        return self._version or "unknown"

    def supports(self, flag: str) -> bool:
        return bool(self._flags and flag in self._flags)

    # -- indexing -----------------------------------------------------------

    def build(self, root: Path) -> IndexResult:
        return self._run(root, incremental=False)

    def update(self, root: Path) -> IndexResult:
        if not self.supports("--update"):
            log.debug("no --update flag; falling back to a full build")
            return self._run(root, incremental=False)
        return self._run(root, incremental=True)

    def query(self, root: Path, q: str) -> list[Node]:
        result = self._load_existing(root)
        if result is None:
            result = self.build(root)
        needle = q.lower()
        return [
            n
            for n in result.nodes
            if needle in n.name.lower() or needle in n.path.lower()
        ]

    def _run(self, root: Path, *, incremental: bool) -> IndexResult:
        cli = ckplat.which(CLI)
        if not cli:
            raise BackendUnavailable(f"{CLI} is not installed", backend=self.name)

        cmd = [str(cli), "."]
        if incremental:
            cmd.append("--update")

        result = ckplat.run(cmd, timeout=BUILD_TIMEOUT, cwd=root)
        if not result.ok:
            raise BackendUnavailable(
                f"{CLI} {self.version} failed ({result.code}): "
                f"{' '.join(cmd)}\n{result.output[:600]}",
                backend=self.name,
            )

        parsed = self._load_existing(root)
        if parsed is None:
            raise BackendUnavailable(
                f"{CLI} {self.version} produced no readable output", backend=self.name
            )
        return parsed

    # -- parsing ------------------------------------------------------------

    def _load_existing(self, root: Path) -> IndexResult | None:
        for candidate in (
            root / "graphify-out" / "graph.json",
            root / ".graphify" / "graph.json",
        ):
            if candidate.is_file():
                try:
                    return self._parse(
                        json.loads(candidate.read_text(encoding="utf-8"))
                    )
                except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
                    raise BackendUnavailable(
                        f"could not parse {candidate}: {exc}", backend=self.name
                    ) from exc
        return None

    def _parse(self, raw: dict) -> IndexResult:
        """Map the tool's native schema onto ours, tolerating shape drift."""
        nodes: list[Node] = []
        for item in raw.get("nodes", []) or []:
            if not isinstance(item, dict):
                continue
            identifier = str(item.get("id") or item.get("name") or "")
            if not identifier:
                continue
            nodes.append(
                Node(
                    id=identifier,
                    kind=_map_kind(str(item.get("type") or item.get("kind") or "")),
                    path=str(item.get("file") or item.get("path") or ""),
                    name=str(item.get("name") or identifier),
                    line=int(item.get("line") or item.get("start_line") or 0),
                )
            )

        edges: list[Edge] = []
        for item in raw.get("edges", []) or raw.get("links", []) or []:
            if not isinstance(item, dict):
                continue
            src = str(item.get("source") or item.get("src") or item.get("from") or "")
            dst = str(item.get("target") or item.get("dst") or item.get("to") or "")
            if src and dst:
                edges.append(
                    Edge(src=src, dst=dst, kind=_map_edge(str(item.get("type") or "")))
                )

        communities: list[Community] = []
        for item in raw.get("communities", []) or []:
            if isinstance(item, dict):
                communities.append(
                    Community(
                        id=str(item.get("id", len(communities))),
                        label=str(item.get("label") or item.get("name") or ""),
                        members=tuple(str(m) for m in item.get("members", []) or []),
                    )
                )

        return IndexResult(
            nodes=nodes,
            edges=edges,
            communities=communities,
            backend_name=self.name,
            generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
            stats={
                "source": CLI,
                "version": self.version,
                "files": len({n.path for n in nodes}),
            },
        )


def has_api_key() -> bool:
    """Is a key present that this backend's semantic extraction can use?"""
    import os

    return any(os.environ.get(var, "").strip() for var in API_KEY_VARS)


def _map_kind(value: str) -> NodeKind:
    lowered = value.lower()
    for kind in (NodeKind.CLASS, NodeKind.METHOD, NodeKind.FUNCTION, NodeKind.MODULE):
        if kind.value in lowered:
            return kind
    if lowered in {"file", "script"}:
        return NodeKind.MODULE
    return NodeKind.UNKNOWN


def _map_edge(value: str) -> EdgeKind:
    lowered = value.lower()
    for kind in (
        EdgeKind.CALLS,
        EdgeKind.CONTAINS,
        EdgeKind.INHERITS,
        EdgeKind.IMPORTS,
    ):
        if kind.value in lowered:
            return kind
    return EdgeKind.IMPORTS


__all__ = ["GraphifyBackend"]
