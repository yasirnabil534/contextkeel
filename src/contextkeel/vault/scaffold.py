"""Create and refresh the notes tree.

Non-destructive by construction: a file is only rewritten when its current
content still matches the fingerprint recorded the last time this tool wrote
it. Anything a human or an agent has since edited is left alone and reported
as drift instead.

``Templates/`` ships verbatim — the ``{{ ... }}`` tokens in those files are
intentional, because they are templates *for humans*. Everything else is
rendered, and no unresolved token may survive into a written note.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from contextkeel.config import Config, summary

log = logging.getLogger("contextkeel")

TEMPLATE_ROOT = Path(__file__).parent / "templates"
VERBATIM_DIRS = {"Templates"}

TREE_DIRS = (
    "Context",
    "Decisions",
    "Knowledge",
    "Daily",
    "Inbox",
    "Templates",
    "attachments",
)


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


@dataclass
class ScaffoldResult:
    created: list[Path] = field(default_factory=list)
    updated: list[Path] = field(default_factory=list)
    preserved: list[Path] = field(default_factory=list)
    fingerprints: dict[str, str] = field(default_factory=dict)

    @property
    def changed(self) -> bool:
        return bool(self.created or self.updated)


def context_for(cfg: Config) -> dict:
    """Values available to every template. No token may go unfilled."""
    return {
        "project_name": cfg.project.name or "This project",
        "description": cfg.project.description,
        "date": date.today().isoformat(),
        "time": "",
        "stack": summary(cfg),
        "frontend": cfg.frontend.model_dump(),
        "backend": cfg.backend.model_dump(),
        "architecture": cfg.architecture.model_dump(),
        "conventions": cfg.conventions.model_dump(),
        "ui": cfg.ui.model_dump(),
    }


def scaffold(
    vault_dir: Path, cfg: Config, known: dict[str, str] | None = None
) -> ScaffoldResult:
    """Create or refresh the notes tree. Idempotent."""
    from jinja2 import StrictUndefined, Template

    known = known or {}
    result = ScaffoldResult()
    values = context_for(cfg)

    vault_dir.mkdir(parents=True, exist_ok=True)
    for name in TREE_DIRS:
        (vault_dir / name).mkdir(parents=True, exist_ok=True)

    for source in sorted(TEMPLATE_ROOT.rglob("*")):
        if source.is_dir():
            continue
        rel = source.relative_to(TEMPLATE_ROOT)
        verbatim = rel.parts[0] in VERBATIM_DIRS

        target_rel = rel.with_suffix("") if source.suffix == ".j2" else rel
        target = vault_dir / target_rel

        raw = source.read_text(encoding="utf-8")
        if verbatim:
            content = raw
        else:
            # StrictUndefined: a missing value is a bug, not a silent blank.
            content = Template(raw, undefined=StrictUndefined).render(**values)
            if "{{" in content:
                raise ValueError(f"unresolved template token in {rel}")

        key = target_rel.as_posix()
        digest = fingerprint(content)

        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            result.created.append(target)
            result.fingerprints[key] = digest
            continue

        current = target.read_text(encoding="utf-8", errors="replace")
        if fingerprint(current) == digest:
            result.fingerprints[key] = digest
            continue

        previous = known.get(key)
        if previous is not None and fingerprint(current) == previous:
            # Untouched since we wrote it — safe to refresh.
            target.write_text(content, encoding="utf-8")
            result.updated.append(target)
            result.fingerprints[key] = digest
        else:
            # Hand-edited. Leave it; report it.
            result.preserved.append(target)
            result.fingerprints[key] = previous or fingerprint(current)

    for keep in ("Knowledge", "Daily", "Inbox", "attachments"):
        marker = vault_dir / keep / ".gitkeep"
        if not marker.exists():
            marker.touch()

    _seed_obsidian_config(vault_dir)
    return result


def _seed_obsidian_config(vault_dir: Path) -> None:
    """Make the folder open cleanly as an Obsidian vault.

    Obsidian would create this itself, but seeding it means a reviewer who
    opens the folder gets sensible settings immediately instead of the
    first-run wizard. Written in code rather than shipped as package data
    because a dot-directory is easy for a build backend to drop silently.

    Never overwrites: these are the user's settings once Obsidian touches them.
    """
    import json

    config_dir = vault_dir / ".obsidian"
    config_dir.mkdir(parents=True, exist_ok=True)
    app = config_dir / "app.json"
    if not app.exists():
        app.write_text(
            json.dumps(
                {
                    "attachmentFolderPath": "attachments",
                    "alwaysUpdateLinks": True,
                    "newFileLocation": "folder",
                    "newFileFolderPath": "Inbox",
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def is_scaffolded(vault_dir: Path) -> bool:
    return (vault_dir / "Context" / "Conventions.md").is_file()


__all__ = [
    "ScaffoldResult",
    "context_for",
    "fingerprint",
    "is_scaffolded",
    "scaffold",
]
