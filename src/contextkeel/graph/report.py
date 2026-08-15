"""Render an index into what agents actually read.

Written for an agent deciding *which files to open*, so it leads with
navigation rather than statistics. Formatting is deterministic and the only
timestamp lives in a single header line, which keeps golden diffs readable.
"""

from __future__ import annotations

import json
from pathlib import Path

from contextkeel.graph.base import IndexResult, NodeKind

TOP_NODES = 15
MAX_COMMUNITY_MEMBERS = 12

HEADER = """# Code index

> Generated — do not edit by hand. Rebuild with `ckeel sync`.
>
> **Agents: read this before opening source files.** It exists so you can
> navigate to the two or three files that matter instead of scanning the tree.
> For a precise lookup, query `index.json` next to this file rather than
> globbing the repository.
"""


def write(result: IndexResult, index_dir: Path) -> tuple[Path, Path]:
    """Write ``REPORT.md`` and ``index.json``. Returns both paths."""
    index_dir.mkdir(parents=True, exist_ok=True)
    report_path = index_dir / "REPORT.md"
    json_path = index_dir / "index.json"

    report_path.write_text(render_markdown(result), encoding="utf-8")
    json_path.write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8"
    )
    return report_path, json_path


def read(index_dir: Path) -> IndexResult | None:
    path = index_dir / "index.json"
    if not path.is_file():
        return None
    try:
        return IndexResult.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        return None


def render_markdown(result: IndexResult) -> str:
    lines: list[str] = [HEADER.rstrip(), ""]
    lines.append(f"_Generated: {result.generated_at or 'unknown'}_")
    lines.append("")

    modules = [n for n in result.nodes if n.kind is NodeKind.MODULE]
    symbols = [n for n in result.nodes if n.kind is not NodeKind.MODULE]

    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Files indexed: **{len(modules)}**")
    lines.append(f"- Symbols: **{len(symbols)}**")
    lines.append(f"- Relationships: **{len(result.edges)}**")
    lines.append(f"- Areas: **{len(result.communities)}**")
    if result.stats.get("truncated"):
        lines.append(
            f"- ⚠ Only the first {result.stats.get('max_files')} files were indexed "
            "(repository is very large)."
        )
    lines.append("")

    lines.append("## Start here")
    lines.append("")
    lines.append("The most connected files — changes here ripple furthest.")
    lines.append("")
    degree = result.degree()
    ranked = sorted(
        (n for n in modules),
        key=lambda n: (-degree.get(n.id, 0), n.path),
    )[:TOP_NODES]
    if ranked:
        for node in ranked:
            lines.append(f"- `{node.path}` — {degree.get(node.id, 0)} connections")
    else:
        lines.append("_No files indexed yet._")
    lines.append("")

    lines.append("## Areas")
    lines.append("")
    if result.communities:
        for community in result.communities:
            members = list(community.members)[:MAX_COMMUNITY_MEMBERS]
            more = len(community.members) - len(members)
            listed = ", ".join(f"`{Path(m).name}`" for m in members)
            suffix = f" _(+{more} more)_" if more > 0 else ""
            lines.append(f"### `{community.label or community.id}`")
            lines.append("")
            lines.append(f"{listed}{suffix}")
            lines.append("")
    else:
        lines.append("_No areas detected._")
        lines.append("")

    lines.append("## Entry points")
    lines.append("")
    entries = [
        n
        for n in modules
        if Path(n.path).stem
        in {"main", "index", "app", "cli", "server", "__main__", "mod"}
    ]
    if entries:
        for node in entries[:TOP_NODES]:
            lines.append(f"- `{node.path}`")
    else:
        lines.append("_None identified by name._")
    lines.append("")

    return "\n".join(lines) + "\n"


__all__ = ["read", "render_markdown", "write"]
