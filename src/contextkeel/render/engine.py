"""Render orchestration.

Writes are atomic, fingerprinted, and non-destructive. Before overwriting a
generated file the engine compares what is on disk against the fingerprint
recorded when this tool last wrote it:

* identical — safe to refresh;
* different — a human edited a generated file. Leave it, and report it.

That rule is why re-running ``init`` is safe, and why a teammate's local tweak
is never silently discarded.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path

from contextkeel.config import Config
from contextkeel.hooks import install as hook_install
from contextkeel.render.model import HookDef, load_content
from contextkeel.render.targets import claude as claude_target
from contextkeel.render.targets import continue_ as continue_target
from contextkeel.render.targets import cursor as cursor_target

log = logging.getLogger("contextkeel")

TARGETS = {
    "claude": claude_target.render,
    "cursor": cursor_target.render,
    "continue": continue_target.render,
}


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


@dataclass
class RenderReport:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    fingerprints: dict[str, str] = field(default_factory=dict)

    @property
    def changed(self) -> bool:
        return bool(self.created or self.updated)

    @property
    def clean(self) -> bool:
        return not self.changed and not self.conflicts

    def summary(self) -> str:
        return (
            f"{len(self.created)} created, {len(self.updated)} updated, "
            f"{len(self.unchanged)} unchanged, {len(self.conflicts)} preserved"
        )


def test_commands_for(cfg: Config) -> list[str]:
    """Permission entries so the mandated workflow does not prompt."""
    framework = cfg.conventions.test_framework
    mapping = {
        "pytest": ["Bash(pytest:*)", "Bash(uv run:*)"],
        "vitest": ["Bash(npm test:*)", "Bash(npx vitest:*)"],
        "jest": ["Bash(npm test:*)", "Bash(npx jest:*)"],
        "go-test": ["Bash(go test:*)"],
        "cargo-test": ["Bash(cargo test:*)"],
        "xunit": ["Bash(dotnet test:*)"],
        "nunit": ["Bash(dotnet test:*)"],
    }
    return mapping.get(framework, [])


def build_files(
    root: Path,
    cfg: Config,
    vault_dir: Path,
    hooks: list[HookDef],
) -> dict[str, str]:
    """Every file this tool generates, as ``relative path -> content``."""
    bundle = load_content()
    allowed = test_commands_for(cfg)

    files: dict[str, str] = {"AGENTS.md": _agents_md(cfg, vault_dir)}
    for name, render_target in TARGETS.items():
        log.debug("rendering target %s", name)
        files.update(
            render_target(
                bundle=bundle,
                root=root,
                vault_dir=vault_dir,
                hooks=hooks,
                allowed_commands=allowed,
            )
        )
    return files


def render(
    root: Path,
    cfg: Config,
    vault_dir: Path,
    hooks: list[HookDef],
    known: dict[str, str] | None = None,
    *,
    check: bool = False,
) -> RenderReport:
    """Render every target. With ``check=True`` nothing is written."""
    known = known or {}
    report = RenderReport()
    files = build_files(root, cfg, vault_dir, hooks)

    for rel, content in sorted(files.items()):
        target = root / rel

        # Normalise mergeable files even when creating them, so the create and
        # update paths emit identical bytes. Otherwise the first render writes
        # unmerged content and the very next one "updates" it, forever.
        if hook_install.is_mergeable(rel) and not target.exists():
            content = hook_install.merge(rel, content, "{}")

        digest = fingerprint(content)

        if not target.exists():
            report.created.append(rel)
            report.fingerprints[rel] = digest
            if not check:
                _write(target, content)
            continue

        current = target.read_text(encoding="utf-8", errors="replace")

        # Shared files: this tool owns some entries, the developer owns others.
        # Merge rather than replace, so their permissions and hooks survive.
        if hook_install.is_mergeable(rel):
            content = hook_install.merge(rel, content, current)
            digest = fingerprint(content)

        current_digest = fingerprint(current)

        if current_digest == digest:
            report.unchanged.append(rel)
            report.fingerprints[rel] = digest
            continue

        previous = known.get(rel)
        if previous is None or current_digest == previous:
            # Either we have never tracked it, or it is untouched since we
            # wrote it. Safe to refresh.
            report.updated.append(rel)
            report.fingerprints[rel] = digest
            if not check:
                _write(target, content)
        else:
            report.conflicts.append(rel)
            report.fingerprints[rel] = previous

    return report


def _write(path: Path, content: str) -> None:
    """Atomic: temp file beside the target, then replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".ckeel-tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _agents_md(cfg: Config, vault_dir: Path) -> str:
    vault_name = vault_dir.name
    return f"""# AGENTS.md

The shared, tool-agnostic source of truth for this repository. Every editor's
configuration is generated from it, so Claude Code, Cursor and Continue all
behave the same way.

Generated by contextkeel — do not edit by hand. Run `ckeel sync` after changes.

## 1. Read context before code

1. `project.yml` — the resolved stack ({cfg.project.type}).
2. `.contextkeel/index/REPORT.md` — architecture overview and where to start.
3. `.contextkeel/index/index.json` — query it for precise lookups instead of
   globbing the repository.
4. `{vault_name}/Context/` — Conventions, Domain Glossary, API Contracts,
   Tech Stack.
5. Only then open source files, guided by what the index told you.

## 2. Plan before building

Given requirements for a new project, module, or large feature, run the
`write-prompt-plan` skill first. It writes a phased, dependency-tracked prompt
list per tier into `.docs/`, with a migration-style registry so several people
can work without colliding. Generating the plan and executing it are separate
steps.

## 3. Conventions

Follow `{vault_name}/Context/Conventions.md`. Match the existing style of the
file you are editing. Small, focused changes. Tests use
**{cfg.conventions.test_framework}**. Commits follow
**{cfg.conventions.commit_style}**. Never commit secrets.

## 4. Keep context in sync

After a meaningful change run `ckeel sync`: it refreshes the code index and the
prescriptive notes. Record significant decisions as an ADR, and prepend a short
plain-language entry to `{vault_name}/Changelog.md` when a feature ships — that
note is for the human returning to the project, not for other agents.

## 5. Under the hood

`ckeel internals` names every underlying tool, prints the exact commands run on
your behalf, and lists every override. Nothing here is hidden — the neutral
wording is a default, not a restriction.
"""


__all__ = [
    "RenderReport",
    "build_files",
    "fingerprint",
    "render",
    "test_commands_for",
]
