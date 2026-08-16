"""MCP tool definitions.

Each delegates to the same functions the CLI calls — there is no second
implementation of anything here, so the two surfaces cannot drift.

Responses are capped and paginated. An unbounded dump would defeat the entire
purpose of the product, which is to spend fewer tokens than reading the files
would have cost.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

MAX_RESULTS = 50
MAX_REPORT_CHARS = 12_000


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "load_context",
        "description": (
            "Load everything you need to start work in this repository: the "
            "resolved stack, a navigation summary of the code index, and the "
            "project's conventions. Call this ONCE at the start of a task "
            "instead of reading a dozen files."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "include_notes": {
                    "type": "boolean",
                    "description": "Include the prescriptive notes. Default true.",
                }
            },
        },
    },
    {
        "name": "query_index",
        "description": (
            "Find where a symbol, file, or module lives, with file:line "
            "results. Use instead of globbing or grepping the repository."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Symbol or path fragment."},
                "limit": {
                    "type": "integer",
                    "description": f"Max results (<= {MAX_RESULTS}).",
                },
                "offset": {"type": "integer", "description": "Skip this many results."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "sync_context",
        "description": "Refresh the code index and project notes after making changes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "full": {"type": "boolean", "description": "Force a full rebuild."}
            },
        },
    },
    {
        "name": "status",
        "description": "Short summary: stack, index freshness, plan progress, latest change.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_notes",
        "description": (
            "List the project's notes: conventions, glossary, API contracts, "
            "decisions and changelog. Use before reading, to see what exists."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "subdir": {
                    "type": "string",
                    "description": "Limit to a subfolder, e.g. 'Context' or 'Decisions'.",
                }
            },
        },
    },
    {
        "name": "read_note",
        "description": (
            "Read one project note by its path relative to the notes folder, "
            "e.g. 'Context/Conventions.md'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "e.g. Context/Conventions.md"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_note",
        "description": (
            "Create or replace one project note. Use for recording decisions, "
            "glossary terms and API contracts as you learn them. Markdown only."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "e.g. Decisions/0003-caching.md",
                },
                "content": {"type": "string", "description": "Full Markdown content."},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "plan",
        "description": (
            "Validate a prompt plan, or allocate a retrofit code for one. "
            "Pass 'check' with a path, or 'insert_after' with a prompt code."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "check": {"type": "string", "description": "Path to a plan file."},
                "insert_after": {"type": "string", "description": "e.g. CK-0009"},
                "tier": {
                    "type": "string",
                    "description": "frontend | backend | mobile",
                },
            },
        },
    },
]


def load_context(root: Path, include_notes: bool = True) -> str:
    from contextkeel.cli.common import open_workspace
    from contextkeel.config import summary

    workspace = open_workspace(root)
    parts = [f"# Context for {workspace.config.project.name}", ""]
    parts.append(f"**Stack:** {summary(workspace.config)}")
    parts.append(f"**Type:** {workspace.config.project.type}")
    parts.append(f"**Tests:** {workspace.config.conventions.test_framework}")
    parts.append("")

    report_path = workspace.layout.index_report
    if report_path.is_file():
        parts.append(report_path.read_text(encoding="utf-8")[:MAX_REPORT_CHARS])
    else:
        parts.append("_No code index yet. Call sync_context first._")

    if include_notes:
        context_dir = workspace.vault_dir / "Context"
        for name in ("Conventions.md", "Domain Glossary.md", "API Contracts.md"):
            path = context_dir / name
            if path.is_file():
                parts.append("")
                parts.append(path.read_text(encoding="utf-8")[:4000])

    return "\n".join(parts)


def query_index(root: Path, query: str, limit: int = 20, offset: int = 0) -> str:
    from contextkeel.cli.common import open_workspace
    from contextkeel.graph import report

    workspace = open_workspace(root)
    result = report.read(workspace.layout.index)
    if result is None:
        return "No code index yet. Call sync_context first."

    needle = query.lower()
    matches = [
        n for n in result.nodes if needle in n.name.lower() or needle in n.path.lower()
    ]
    limit = max(1, min(limit, MAX_RESULTS))
    page = matches[offset : offset + limit]
    if not page:
        return f"No matches for {query!r} among {len(result.nodes)} indexed entries."

    lines = [
        f"{len(matches)} match(es) for {query!r}; showing {offset + 1}-{offset + len(page)}:"
    ]
    lines.extend(
        f"- {n.path}:{n.line} — {n.kind}: {n.name}"
        if n.line
        else f"- {n.path} — {n.kind}"
        for n in page
    )
    if offset + len(page) < len(matches):
        lines.append(f"…{len(matches) - offset - len(page)} more (raise offset).")
    return "\n".join(lines)


def sync_context(root: Path, full: bool = False) -> str:
    from contextkeel.cli import sync as sync_cmd

    code = sync_cmd.run(root, full=full)
    return "Context refreshed." if code == 0 else "Context refresh reported problems."


def status(root: Path) -> str:
    from contextkeel.cli.common import open_workspace
    from contextkeel.config import summary
    from contextkeel.graph import report

    workspace = open_workspace(root)
    index = report.read(workspace.layout.index)
    return "\n".join(
        [
            f"Project: {workspace.config.project.name}",
            f"Stack: {summary(workspace.config)}",
            f"Index: {len(index.nodes) if index else 0} entries",
            f"Last sync: {workspace.state.last_sync or 'never'}",
        ]
    )


def plan(
    root: Path, check: str = "", insert_after: str = "", tier: str = "backend"
) -> str:
    from contextkeel.cli import plan as plan_cmd

    if check:
        path = Path(check)
        if not path.is_absolute():
            path = root / check
        if not path.is_file():
            return f"No such plan: {path}"
        problems = plan_cmd.validate(path.read_text(encoding="utf-8", errors="replace"))
        return (
            "Plan is well-formed."
            if not problems
            else "Problems:\n- " + "\n- ".join(problems)
        )

    if insert_after:
        target = root / ".docs" / f"{tier}_prompt_list.md"
        if not target.is_file():
            return f"No plan at {target}"
        code = plan_cmd.next_retrofit_code(
            target.read_text(encoding="utf-8"), insert_after
        )
        return f"Use {code} for the retrofit after {insert_after}."

    return "Pass 'check' with a plan path, or 'insert_after' with a prompt code."


def _vault_of(root: Path) -> Path:
    from contextkeel.cli.common import open_workspace

    return open_workspace(root).vault_dir


def _safe_note_path(root: Path, rel: str) -> Path:
    """Resolve ``rel`` inside the notes folder, or refuse.

    An MCP tool takes its path from a model, so ``../../.ssh/id_rsa`` is a
    realistic input rather than a hypothetical one. Resolve first, then verify
    containment -- checking the string for ".." is not equivalent, because
    symlinks and absolute paths bypass it.
    """
    vault = _vault_of(root).resolve()
    candidate = (vault / rel).resolve()
    if not candidate.is_relative_to(vault):
        raise ValueError(f"path escapes the notes folder: {rel}")
    if candidate.suffix.lower() not in {".md", ""}:
        raise ValueError("notes are Markdown; use a .md path")
    return candidate.with_suffix(".md") if not candidate.suffix else candidate


def list_notes(root: Path, subdir: str = "") -> str:
    vault = _vault_of(root)
    base = _safe_note_path(root, subdir).with_suffix("") if subdir else vault
    if not base.is_dir():
        return f"No such folder: {subdir or '.'}"
    found = sorted(
        path.relative_to(vault).as_posix()
        for path in base.rglob("*.md")
        if ".obsidian" not in path.parts
    )
    if not found:
        return "No notes yet."
    return f"{len(found)} note(s):\n" + "\n".join(f"- {name}" for name in found)


def read_note(root: Path, path: str) -> str:
    target = _safe_note_path(root, path)
    if not target.is_file():
        return f"No such note: {path}. Call list_notes to see what exists."
    text = target.read_text(encoding="utf-8", errors="replace")
    return text[:MAX_REPORT_CHARS]


def write_note(root: Path, path: str, content: str) -> str:
    target = _safe_note_path(root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    existed = target.is_file()
    tmp = target.with_name(target.name + ".ckeel-tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(target)
    verb = "Updated" if existed else "Created"
    return f"{verb} {target.relative_to(_vault_of(root)).as_posix()}"


HANDLERS = {
    "list_notes": list_notes,
    "read_note": read_note,
    "write_note": write_note,
    "load_context": load_context,
    "query_index": query_index,
    "sync_context": sync_context,
    "status": status,
    "plan": plan,
}


__all__ = ["HANDLERS", "MAX_RESULTS", "TOOL_SCHEMAS"]
