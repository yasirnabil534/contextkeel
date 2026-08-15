"""Backend-neutral code-index interface.

No type or field name in this module may reference a specific third-party
tool: that is what lets one backend be swapped for another without any caller
noticing, and it is why an upstream package disappearing degrades this product
instead of breaking it.

All collections are sorted deterministically on construction so golden tests
stay stable across runs, machines and platforms.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable


class NodeKind(StrEnum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    UNKNOWN = "unknown"


class EdgeKind(StrEnum):
    IMPORTS = "imports"
    CALLS = "calls"
    CONTAINS = "contains"
    INHERITS = "inherits"


@dataclass(frozen=True, order=True)
class Node:
    id: str
    kind: NodeKind = NodeKind.UNKNOWN
    path: str = ""
    name: str = ""
    line: int = 0


@dataclass(frozen=True, order=True)
class Edge:
    src: str
    dst: str
    kind: EdgeKind = EdgeKind.IMPORTS


@dataclass(frozen=True, order=True)
class Community:
    id: str
    label: str = ""
    members: tuple[str, ...] = ()


@dataclass
class IndexResult:
    """What every backend returns, whatever it is underneath."""

    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    communities: list[Community] = field(default_factory=list)
    stats: dict[str, object] = field(default_factory=dict)
    backend_name: str = ""
    generated_at: str = ""

    def __post_init__(self) -> None:
        # Deterministic ordering is part of the contract, not a nicety.
        self.nodes = sorted(set(self.nodes))
        self.edges = sorted(set(self.edges))
        self.communities = sorted(set(self.communities))

    @property
    def is_empty(self) -> bool:
        return not self.nodes

    def degree(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for edge in self.edges:
            counts[edge.src] = counts.get(edge.src, 0) + 1
            counts[edge.dst] = counts.get(edge.dst, 0) + 1
        return counts

    def to_dict(self) -> dict:
        return {
            "backend_name": self.backend_name,
            "generated_at": self.generated_at,
            "stats": self.stats,
            "nodes": [asdict(n) for n in self.nodes],
            "edges": [asdict(e) for e in self.edges],
            "communities": [asdict(c) for c in self.communities],
        }

    @classmethod
    def from_dict(cls, data: dict) -> IndexResult:
        return cls(
            nodes=[
                Node(
                    id=n["id"],
                    kind=NodeKind(n.get("kind", "unknown")),
                    path=n.get("path", ""),
                    name=n.get("name", ""),
                    line=n.get("line", 0),
                )
                for n in data.get("nodes", [])
            ],
            edges=[
                Edge(
                    src=e["src"],
                    dst=e["dst"],
                    kind=EdgeKind(e.get("kind", "imports")),
                )
                for e in data.get("edges", [])
            ],
            communities=[
                Community(
                    id=c["id"],
                    label=c.get("label", ""),
                    members=tuple(c.get("members", ())),
                )
                for c in data.get("communities", [])
            ],
            stats=data.get("stats", {}),
            backend_name=data.get("backend_name", ""),
            generated_at=data.get("generated_at", ""),
        )


@runtime_checkable
class GraphBackend(Protocol):
    """One way of turning a repository into an :class:`IndexResult`.

    Implementations raise :class:`~contextkeel.errors.BackendUnavailable` on
    failure. They never call ``sys.exit`` and never print — presentation is
    the caller's job, and a backend that writes to stdout would corrupt both
    ``--json`` output and the MCP protocol stream.
    """

    #: Stable identifier used in state, ``--backend`` and diagnostics.
    name: str
    #: Higher wins during selection.
    priority: int

    def is_available(self) -> bool: ...

    def build(self, root: Path) -> IndexResult: ...

    def update(self, root: Path) -> IndexResult: ...

    def query(self, root: Path, q: str) -> list[Node]: ...


__all__ = [
    "Community",
    "Edge",
    "EdgeKind",
    "GraphBackend",
    "IndexResult",
    "Node",
    "NodeKind",
]
