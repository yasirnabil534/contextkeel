"""Changelog entries and ADR allocation.

The changelog is written for the human coming back to the project after a
week, so entries are prose. File lists and diff fragments are rejected: the
code index already answers "what is the structure", and git already answers
"what changed line by line".

Dates are local, not UTC, so an entry matches the developer's day.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

MARKER = "<!-- ckeel:entries -->"
_ADR_NAME = re.compile(r"^(\d{4})-")
_PATHISH = re.compile(r"(^|\s)(?:[\w./-]+/[\w./-]+\.\w+|[-+]{3}\s)")


class ChangelogError(ValueError):
    """The proposed entry is not written for a human."""


def prepend_entry(path: Path, title: str, sentences: str) -> None:
    """Insert a dated entry directly below the intro block, newest first."""
    text = _reject_machine_prose(sentences)
    entry = f"## {date.today().isoformat()} — {title}\n{text.strip()}\n"

    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Changelog\n\n{MARKER}\n\n{entry}", encoding="utf-8")
        return

    existing = path.read_text(encoding="utf-8", errors="replace")
    if MARKER in existing:
        head, _, tail = existing.partition(MARKER)
        updated = f"{head}{MARKER}\n\n{entry}{tail.lstrip(chr(10))}"
    else:
        # No marker (hand-edited file): insert above the first existing entry.
        match = re.search(r"^## ", existing, re.M)
        if match:
            updated = (
                existing[: match.start()] + entry + "\n" + existing[match.start() :]
            )
        else:
            updated = existing.rstrip("\n") + "\n\n" + entry
    path.write_text(updated, encoding="utf-8")


def _reject_machine_prose(text: str) -> str:
    if _PATHISH.search(text):
        raise ChangelogError(
            "changelog entries are for a human: no file paths or diffs"
        )
    if len(re.findall(r"[.!?]", text)) > 4:
        raise ChangelogError("keep changelog entries to 1-3 sentences")
    return text


def next_adr_number(decisions_dir: Path) -> int:
    """Next free ADR number. Handles gaps and an empty directory."""
    highest = 0
    if decisions_dir.is_dir():
        for path in decisions_dir.glob("*.md"):
            match = _ADR_NAME.match(path.name)
            if match:
                highest = max(highest, int(match.group(1)))
    return highest + 1


def slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower()).strip()
    return re.sub(r"[\s_]+", "-", slug)[:60] or "decision"


def create_adr(
    decisions_dir: Path,
    title: str,
    *,
    context: str = "",
    decision: str = "",
    consequences: str = "",
    alternatives: str = "",
) -> Path:
    """Write a numbered ADR with a real date and a slugified filename."""
    decisions_dir.mkdir(parents=True, exist_ok=True)
    number = next_adr_number(decisions_dir)
    today = date.today().isoformat()
    path = decisions_dir / f"{number:04d}-{slugify(title)}.md"

    path.write_text(
        f"""---
created: {today}
type: decision
tags: [adr]
status: accepted
---

# {number:04d} — {title}

**Status:** accepted
**Date:** {today}

## Context

{context or "_Not recorded._"}

## Decision

{decision or "_Not recorded._"}

## Consequences

{consequences or "_Not recorded._"}

## Alternatives considered

{alternatives or "_Not recorded._"}
""",
        encoding="utf-8",
    )
    return path


__all__ = [
    "MARKER",
    "ChangelogError",
    "create_adr",
    "next_adr_number",
    "prepend_entry",
    "slugify",
]
