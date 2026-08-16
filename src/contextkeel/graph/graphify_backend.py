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
import os
import re
from datetime import UTC, datetime
from enum import StrEnum
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

#: Keys that unlock semantic extraction of documentation files. They are a
#: bonus, not a requirement: see IndexMode below.
API_KEY_VARS = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "MOONSHOT_API_KEY",
    "DEEPSEEK_API_KEY",
)


class IndexMode(StrEnum):
    """How to run the preferred indexer on this machine.

    It only needs an LLM for *summarising documentation*, which this tool does
    not use -- we want a code map for navigation. So a missing API key is not
    a reason to fall back; it just selects a cheaper mode.
    """

    #: An API key is set: full extraction, documentation included.
    FULL = "full"
    #: Drive the local `claude` binary instead of an API key. Free of API
    #: billing but spends the user's subscription quota, so it is opt-in.
    CLAUDE_CLI = "claude-cli"
    #: Local AST parse only. No key, no network, no quota. The default.
    CODE_ONLY = "code-only"


def has_api_key() -> bool:
    """Is a key present that semantic extraction could use?"""
    return any(os.environ.get(var, "").strip() for var in API_KEY_VARS)


def claude_cli_available() -> bool:
    """Is the Claude Code CLI installed? It authenticates by subscription."""
    return ckplat.which("claude") is not None


def resolve_mode(*, use_claude_cli: bool = False) -> IndexMode:
    if has_api_key():
        return IndexMode.FULL
    if use_claude_cli and claude_cli_available():
        return IndexMode.CLAUDE_CLI
    return IndexMode.CODE_ONLY


class GraphifyBackend:
    """Wraps the external indexer CLI."""

    name = "graphify"
    priority = 100

    def __init__(
        self, *, allow_install: bool = True, use_claude_cli: bool = False
    ) -> None:
        self._allow_install = allow_install
        self.mode = resolve_mode(use_claude_cli=use_claude_cli)
        self._version: str | None = None
        self._flags: set[str] | None = None
        self._install_attempted = False

    # -- availability -------------------------------------------------------

    def is_available(self) -> bool:
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

        # A cached selection skips is_available(), so the flag probe may not
        # have run yet. Without this, supports() answers False for everything
        # and the code-only path would never engage after the first run.
        if self._flags is None:
            self._probe()

        cmd = [str(cli), "."]
        if incremental and self.supports("--update"):
            cmd.append("--update")

        if self.mode is IndexMode.CODE_ONLY:
            if not self.supports("--code-only"):
                # An older build cannot skip documentation, and without a key
                # it would abort mid-run. Step aside for the bundled indexer.
                raise BackendUnavailable(
                    f"{CLI} {self.version} has no --code-only and no API key is set",
                    backend=self.name,
                )
            cmd.append("--code-only")
        elif self.mode is IndexMode.CLAUDE_CLI:
            cmd += ["--backend", "claude-cli"]

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
        """Map the tool's native schema onto ours, tolerating shape drift.

        The native format is networkx node-link: nodes carry ``label``,
        ``source_file`` and ``source_location`` (e.g. "L12"), edges live under
        ``links`` with a ``relation``, and community membership is an integer
        on each node rather than a separate list. Alternative key names are
        still accepted so a schema change degrades rather than breaks.
        """
        nodes: list[Node] = []
        for item in raw.get("nodes", []) or []:
            if not isinstance(item, dict):
                continue
            identifier = str(item.get("id") or item.get("label") or "")
            if not identifier:
                continue
            nodes.append(
                Node(
                    id=identifier,
                    kind=_node_kind(item),
                    path=str(
                        item.get("source_file")
                        or item.get("file")
                        or item.get("path")
                        or ""
                    ),
                    name=str(item.get("label") or item.get("name") or identifier),
                    line=_line_of(item),
                )
            )

        edges: list[Edge] = []
        for item in raw.get("links", []) or raw.get("edges", []) or []:
            if not isinstance(item, dict):
                continue
            src = str(item.get("source") or item.get("src") or item.get("from") or "")
            dst = str(item.get("target") or item.get("dst") or item.get("to") or "")
            if src and dst:
                edges.append(
                    Edge(
                        src=src,
                        dst=dst,
                        kind=_map_edge(
                            str(item.get("relation") or item.get("type") or "")
                        ),
                    )
                )

        communities = _communities_from(raw, nodes)

        return IndexResult(
            nodes=nodes,
            edges=edges,
            communities=communities,
            backend_name=self.name,
            generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
            stats={
                "source": CLI,
                "version": self.version,
                "mode": str(self.mode),
                "files": len({n.path for n in nodes if n.path}),
            },
        )


_LINE_RE = re.compile(r"(\d+)")


def _line_of(item: dict) -> int:
    """``source_location`` is a string like "L12"; ``line`` may also appear."""
    for key in ("line", "start_line"):
        value = item.get(key)
        if isinstance(value, int):
            return value
    match = _LINE_RE.search(str(item.get("source_location") or ""))
    return int(match.group(1)) if match else 0


def _node_kind(item: dict) -> NodeKind:
    """Kind is implied by flags rather than stated outright."""
    if item.get("_callable_class"):
        return NodeKind.CLASS
    if item.get("_callable"):
        name = str(item.get("label") or "")
        return NodeKind.METHOD if name.startswith(".") else NodeKind.FUNCTION
    if item.get("file_type") or item.get("source_file"):
        return NodeKind.MODULE
    return _map_kind(str(item.get("type") or item.get("kind") or ""))


def _communities_from(raw: dict, nodes: list[Node]) -> list[Community]:
    """Prefer an explicit list; otherwise group by the per-node community id."""
    explicit = raw.get("communities") or []
    if explicit:
        out: list[Community] = []
        for index, item in enumerate(explicit):
            if isinstance(item, dict):
                out.append(
                    Community(
                        id=str(item.get("id", index)),
                        label=str(item.get("label") or item.get("name") or ""),
                        members=tuple(str(m) for m in item.get("members", []) or []),
                    )
                )
        return out

    by_id = {n.id: n for n in nodes}
    buckets: dict[str, list[str]] = {}
    for item in raw.get("nodes", []) or []:
        if not isinstance(item, dict) or item.get("community") is None:
            continue
        node_id = str(item.get("id") or "")
        if node_id in by_id:
            buckets.setdefault(str(item["community"]), []).append(node_id)

    # Name each group after the directory its members share, which is far
    # more useful to an agent than "Community 3".
    result: list[Community] = []
    for key, members in sorted(
        buckets.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0
    ):
        dirs = {
            (by_id[m].path.rsplit("/", 1)[0] if "/" in by_id[m].path else ".")
            for m in members
            if by_id[m].path
        }
        label = dirs.pop() if len(dirs) == 1 else f"Area {key}"
        result.append(Community(id=key, label=label, members=tuple(sorted(members))))
    return result


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


__all__ = [
    "API_KEY_VARS",
    "GraphifyBackend",
    "IndexMode",
    "claude_cli_available",
    "has_api_key",
    "resolve_mode",
]
