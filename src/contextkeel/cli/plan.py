"""``ckeel plan`` — prompt plans as code, not as a formatting convention.

The registry format only works if it is exact: every code in the table has a
matching block, pointers resolve, and the box borders line up. Leaving that to
prose instructions means it drifts. Here the alignment is computed and the
invariants are checked.

Retrofits use a letter suffix (``CK-0009A``) inserted after the code they
follow, so a missed requirement never renumbers the rest of the plan — the
same discipline as a hand-inserted database migration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from contextkeel import console

BOX_WIDTH = 77
CODE_RE = re.compile(r"\b([A-Z]{2,4})-(\d{4})([A-Z]?)\b")
REGISTRY_ROW = re.compile(r"^#\s+([A-Z]{2,4}-\d{4}[A-Z]?)\s*│", re.M)
BLOCK_ID = re.compile(r"PROMPT ID\s*:\s*([A-Z]{2,4}-\d{4}[A-Z]?)")
DEPENDS = re.compile(r"DEPENDS ON\s*:\s*(\S+)")
NEXT = re.compile(r"NEXT\s*:\s*(\S+)")

TIERS = {
    "frontend": ("FE", "Frontend Tier"),
    "backend": ("BE", "Backend Tier"),
    "mobile": ("MOB", "Mobile Tier"),
}


@dataclass
class PromptEntry:
    code: str
    scope: str
    scope_name: str
    title: str
    files: list[str] = field(default_factory=list)
    body: str = ""
    verify: str = ""
    depends: str = "—"
    next_code: str = "—"
    status: str = "[ ] PENDING"
    critical: bool = False


# --------------------------------------------------------------------------
# Rendering — alignment is computed, never hand-counted
# --------------------------------------------------------------------------


def _line(text: str) -> str:
    return "│" + text.ljust(BOX_WIDTH)[:BOX_WIDTH] + "│"


def render_box(entry: PromptEntry) -> str:
    rows = [
        f"  PROMPT ID  : {entry.code}",
        f"  SCOPE      : {entry.scope} — {entry.scope_name}",
        f"  TITLE      : {'★ ' if entry.critical else ''}{entry.title}",
        f"  DEPENDS ON : {entry.depends}",
        f"  NEXT       : {entry.next_code}",
    ]
    if entry.files:
        rows.append(f"  FILES      : {entry.files[0]}")
        rows.extend(f"               {f}" for f in entry.files[1:])
    rows.append(f"  STATUS     : {entry.status}")
    return "\n".join(
        [
            "┌" + "─" * BOX_WIDTH + "┐",
            *[_line(r) for r in rows],
            "└" + "─" * BOX_WIDTH + "┘",
        ]
    )


def render_plan(project: str, tier: str, entries: list[PromptEntry]) -> str:
    prefix, label = TIERS.get(tier, ("BE", "Backend Tier"))
    link_pointers(entries)

    out: list[str] = [
        f"# {project} — {label}",
        "# AI Prompt List for Junior Developers / Agents",
        "# " + "─" * 77,
        "# RUNNING A PROMPT:",
        "# 1. Find the LOWEST prompt with STATUS: [ ] PENDING in the registry below",
        "#    (within your assigned scope, if working alongside others).",
        "# 2. Mark it [~] IN PROGRESS (your initials) and commit that one-line change.",
        "# 3. Copy that prompt's full block into your AI chat exactly as written.",
        "# 4. Review the output, run the VERIFY command, fix any errors.",
        "# 5. Mark it [x] DONE in the registry (note any deviation) and commit.",
        "#",
        "# CONCURRENCY: this registry is the shared source of truth — treat it like a",
        "#   migrations table. Claim only the lowest PENDING code in your scope, and",
        "#   commit registry edits immediately so others see them. To insert a missed",
        f"#   prompt later, run: ckeel plan --insert-after {prefix}-0009",
        "# " + "─" * 77,
        "",
        "# " + "═" * 77,
        "# MIGRATION REGISTRY  —  mark each prompt [x] DONE after execution",
        "# " + "═" * 77,
        "#",
        "#  CODE      │ SCOPE │ TITLE" + " " * 46 + "│ STATUS",
        "# " + "─" * 10 + "┼" + "─" * 7 + "┼" + "─" * 52 + "┼" + "─" * 10,
    ]

    last_scope = None
    for entry in entries:
        if last_scope is not None and entry.scope != last_scope:
            out.append(
                "# " + "─" * 10 + "┼" + "─" * 7 + "┼" + "─" * 52 + "┼" + "─" * 10
            )
        last_scope = entry.scope
        title = ("★ " if entry.critical else "") + entry.title
        if len(title) > 50:
            title = title[:47] + "..."
        out.append(
            f"#  {entry.code:<9}│  {entry.scope:<4} │ {title:<50} │ {entry.status}"
        )
    out.append("# " + "─" * 10 + "┴" + "─" * 7 + "┴" + "─" * 52 + "┴" + "─" * 10)
    out.append(f"# {len(entries)} prompts.")

    shown: set[str] = set()
    for entry in entries:
        if entry.scope not in shown:
            shown.add(entry.scope)
            out.append("")
            out.append("═" * 80)
            out.append(f"SCOPE {entry.scope[1:]} — {entry.scope_name.upper()}")
            out.append("═" * 80)
        out.append("")
        out.append(render_box(entry))
        out.append("")
        out.append(entry.body.strip() or "_To be written._")
        if entry.verify:
            out.append("")
            out.append(f"[VERIFY] {entry.verify}")

    return "\n".join(out) + "\n"


def link_pointers(entries: list[PromptEntry]) -> None:
    """Recompute DEPENDS ON / NEXT from list order."""
    for index, entry in enumerate(entries):
        entry.depends = entries[index - 1].code if index > 0 else "—"
        entry.next_code = (
            entries[index + 1].code if index + 1 < len(entries) else "— (end of plan)"
        )


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


def validate(text: str) -> list[str]:
    """Return a list of problems. Empty means the plan is well-formed."""
    problems: list[str] = []
    registry = REGISTRY_ROW.findall(text)
    blocks = BLOCK_ID.findall(text)

    missing_blocks = [c for c in registry if c not in blocks]
    orphan_blocks = [c for c in blocks if c not in registry]
    if missing_blocks:
        problems.append(f"registry codes with no block: {', '.join(missing_blocks)}")
    if orphan_blocks:
        problems.append(f"blocks not in the registry: {', '.join(orphan_blocks)}")

    duplicates = {c for c in registry if registry.count(c) > 1}
    if duplicates:
        problems.append(f"duplicate codes: {', '.join(sorted(duplicates))}")

    known = set(blocks)
    for pointer_re, label in ((DEPENDS, "DEPENDS ON"), (NEXT, "NEXT")):
        for target in pointer_re.findall(text):
            cleaned = target.strip()
            if cleaned in {"—", "-"} or not CODE_RE.match(cleaned):
                continue
            if cleaned not in known:
                problems.append(f"{label} points at unknown code {cleaned}")

    widths = {
        len(line) for line in text.splitlines() if line.startswith(("│", "┌", "└"))
    }
    if len(widths) > 1:
        problems.append(f"box borders are misaligned (widths: {sorted(widths)})")

    return problems


def next_retrofit_code(text: str, after: str) -> str:
    """``CK-0009`` -> ``CK-0009A``; ``CK-0009A`` -> ``CK-0009B``."""
    match = CODE_RE.match(after)
    if not match:
        raise ValueError(f"not a prompt code: {after}")
    prefix, number, suffix = match.groups()
    existing = {
        m.group(3)
        for m in (CODE_RE.match(c) for c in REGISTRY_ROW.findall(text))
        if m and m.group(1) == prefix and m.group(2) == number and m.group(3)
    }
    letter = "A"
    while letter in existing:
        letter = chr(ord(letter) + 1)
    return f"{prefix}-{number}{letter}" if not suffix else f"{prefix}-{number}{letter}"


# --------------------------------------------------------------------------
# Command
# --------------------------------------------------------------------------


def run(
    root: Path | None = None,
    *,
    requirements: str = "",
    tier: str = "backend",
    check: str = "",
    insert_after: str = "",
) -> int:
    from contextkeel.cli.common import open_workspace

    workspace = open_workspace(root)
    docs = workspace.layout.docs

    if check:
        path = Path(check)
        if not path.is_absolute():
            path = workspace.root / check
        if not path.is_file():
            console.fail(f"no such plan: {path}")
            return 1
        problems = validate(path.read_text(encoding="utf-8", errors="replace"))
        if problems:
            for problem in problems:
                console.fail(problem)
            return 1
        console.ok(f"{path.name} is well-formed.")
        return 0

    if insert_after:
        target = docs / f"{tier}_prompt_list.md"
        if not target.is_file():
            console.fail(f"no plan at {target}")
            return 1
        text = target.read_text(encoding="utf-8")
        code = next_retrofit_code(text, insert_after)
        console.ok(f"Next retrofit code after {insert_after} is {code}.")
        console.say(
            "Add its block directly after that code and re-run "
            f"`ckeel plan --check {target.name}`."
        )
        return 0

    if not requirements:
        console.fail("nothing to plan: pass requirements text or a file path")
        return 1

    prefix, _ = TIERS.get(tier, ("BE", "Backend Tier"))
    entries = _skeleton(prefix, requirements)
    docs.mkdir(parents=True, exist_ok=True)
    target = docs / f"{tier}_prompt_list.md"
    target.write_text(
        render_plan(
            workspace.config.project.name or workspace.root.name, tier, entries
        ),
        encoding="utf-8",
    )
    console.ok(f"Wrote {target.relative_to(workspace.root)} ({len(entries)} prompts).")
    console.say("Fill in each prompt body, then run `ckeel plan --check`.")
    return 0


def _skeleton(prefix: str, requirements: str) -> list[PromptEntry]:
    """One prompt per requirement line, ready for an agent to flesh out."""
    lines = [
        line.strip(" -*\t") for line in requirements.splitlines() if line.strip(" -*\t")
    ]
    entries = [
        PromptEntry(
            code=f"{prefix}-0000",
            scope="S0",
            scope_name="Environment Setup",
            title="Repository and toolchain setup",
            body="Run these commands manually (do NOT paste into the AI):\n\n"
            "```bash\n# toolchain + directory skeleton\n```",
            verify="the project builds and its test command runs",
        )
    ]
    for index, line in enumerate(lines, start=1):
        entries.append(
            PromptEntry(
                code=f"{prefix}-{index:04d}",
                scope="S1",
                scope_name="Implementation",
                title=line[:60],
                body=line,
                verify="",
            )
        )
    return entries


__all__ = [
    "BOX_WIDTH",
    "PromptEntry",
    "link_pointers",
    "next_retrofit_code",
    "render_box",
    "render_plan",
    "run",
    "validate",
]
