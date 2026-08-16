"""Section-level note editing.

These notes are updated repeatedly by ``sync`` and by agents, so updates must
*merge*. Blindly rewriting a file would destroy anything a human added, which
is the fastest way to make people stop trusting the notes.

Round-trip safe: parse then write with no edits produces an identical file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
_HEADING = re.compile(r"^(##\s+.+)$", re.M)


@dataclass
class Note:
    frontmatter: str = ""
    preamble: str = ""
    sections: list[tuple[str, str]] = field(default_factory=list)

    def render(self) -> str:
        parts: list[str] = []
        if self.frontmatter:
            parts.append(f"---\n{self.frontmatter}\n---\n")
        if self.preamble:
            parts.append(self.preamble)
        for heading, body in self.sections:
            parts.append(f"{heading}\n{body}")
        return "".join(parts)

    def find(self, heading: str) -> int:
        wanted = heading.strip().lstrip("#").strip().lower()
        for index, (existing, _) in enumerate(self.sections):
            if existing.lstrip("#").strip().lower() == wanted:
                return index
        return -1


def parse(text: str) -> Note:
    note = Note()
    match = _FRONTMATTER.match(text)
    if match:
        note.frontmatter = match.group(1)
        text = text[match.end() :]

    positions = [m.start() for m in _HEADING.finditer(text)]
    if not positions:
        note.preamble = text
        return note

    note.preamble = text[: positions[0]]
    bounds = positions + [len(text)]
    for index in range(len(positions)):
        chunk = text[bounds[index] : bounds[index + 1]]
        heading, _, body = chunk.partition("\n")
        note.sections.append((heading, body))
    return note


def load(path: Path) -> Note:
    if not path.is_file():
        return Note()
    return parse(path.read_text(encoding="utf-8", errors="replace"))


def save(note: Note, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(note.render(), encoding="utf-8")
    tmp.replace(path)


def upsert_section(note: Note, heading: str, body: str) -> Note:
    """Replace one section, preserving every other one — including user additions."""
    heading = heading if heading.startswith("#") else f"## {heading}"
    body = body if body.endswith("\n") else body + "\n"
    if not body.startswith("\n"):
        body = "\n" + body

    index = note.find(heading)
    if index >= 0:
        note.sections[index] = (heading, body)
    else:
        note.sections.append((heading, body))
    return note


def add_glossary_term(path: Path, term: str, definition: str) -> bool:
    """Insert a term alphabetically. Returns False if it was already present."""
    note = load(path)
    index = note.find("Terms")
    entries: list[str] = []
    if index >= 0:
        entries = [
            line
            for line in note.sections[index][1].splitlines()
            if line.startswith("- **")
        ]

    if any(line.lower().startswith(f"- **{term.lower()}**") for line in entries):
        return False

    entries.append(f"- **{term}** — {definition}")
    entries.sort(key=str.lower)
    upsert_section(note, "Terms", "\n".join(entries))
    save(note, path)
    return True


def upsert_contract(path: Path, name: str, body: str) -> None:
    """Record or update one API contract by name."""
    note = load(path)
    upsert_section(note, f"### {name}" if not name.startswith("#") else name, body)
    save(note, path)


__all__ = [
    "Note",
    "add_glossary_term",
    "load",
    "parse",
    "save",
    "upsert_contract",
    "upsert_section",
]
