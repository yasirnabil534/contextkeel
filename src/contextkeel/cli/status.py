"""``ckeel status`` — a five-line answer to "where is this project?".

Read-only and fast: no index build, no network, no writes. Safe to wire into a
shell prompt or an editor status line.
"""

from __future__ import annotations

import re
from pathlib import Path

from contextkeel import console
from contextkeel.cli.common import open_workspace
from contextkeel.config import summary
from contextkeel.graph import report


def run(root: Path | None = None, *, json_mode: bool = False) -> int:
    workspace = open_workspace(root)

    index = report.read(workspace.layout.index)
    index_line = (
        f"{len(index.nodes)} entries, updated {workspace.state.last_sync or 'never'}"
        if index
        else "not built yet — run `ckeel sync`"
    )

    pending, done = _plan_progress(workspace.layout.docs)
    latest = _latest_changelog(workspace.vault_dir / "Changelog.md")

    if json_mode:
        console.emit_json(
            {
                "project": workspace.config.project.name,
                "stack": summary(workspace.config),
                "index": {
                    "entries": len(index.nodes) if index else 0,
                    "last_sync": workspace.state.last_sync,
                    "backend": workspace.state.selected_backend,
                    "degraded": workspace.state.backend_degraded,
                },
                "plan": {"pending": pending, "done": done},
                "latest_change": latest,
            }
        )
        return 0

    console.say(f"Project : {workspace.config.project.name}")
    console.say(f"Stack   : {summary(workspace.config)}")
    console.say(f"Index   : {index_line}")
    if pending or done:
        console.say(f"Plan    : {done} done, {pending} pending")
    if latest:
        console.say(f"Latest  : {latest}")

    # Reviewing rather than building? These are the two things to open.
    graph_html = workspace.root / "graphify-out" / "graph.html"
    if graph_html.is_file():
        console.say(
            f"Review  : open {graph_html.name} in a browser, {workspace.vault_dir.name}/ for notes"
        )
    else:
        console.say(
            f"Review  : {workspace.vault_dir.name}/ for notes (run `ckeel sync` for the code map)"
        )
    console.detail(
        f"backend={workspace.state.selected_backend} "
        f"degraded={workspace.state.backend_degraded}"
    )
    return 0


# A registry row, not any commented line: the plan's own header explains the
# `[x] DONE` convention, and counting those instructions as progress inflates
# the total by a few prompts.
_REGISTRY_ROW = re.compile(
    r"^#\s+[A-Z]{2,4}-\d{4}[A-Z]?\s*│.*│\s*\[(?P<mark>[ x~])\]", re.M
)


def _plan_progress(docs_dir: Path) -> tuple[int, int]:
    pending = done = 0
    if not docs_dir.is_dir():
        return 0, 0
    for path in docs_dir.glob("*_prompt_list.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in _REGISTRY_ROW.finditer(text):
            if match.group("mark") == "x":
                done += 1
            else:
                pending += 1
    return pending, done


def _latest_changelog(path: Path) -> str:
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            return line[3:].strip()
    return ""


__all__ = ["run"]
