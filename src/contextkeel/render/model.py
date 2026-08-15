"""The canonical agent-config model.

Every editor's configuration is generated from these objects, which is what
makes mirror-drift structurally impossible: a skill's description or its
invocation flag exists in exactly one place, and the targets only decide how
to *shape* it.

Nothing here may exist because one particular editor wants it. Tool-specific
concerns live in :mod:`contextkeel.render.targets`, gated by
:class:`TargetCapabilities`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

CONTENT_ROOT = Path(__file__).parent / "content"

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)


def _split(text: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, text
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, match.group(2)


def _as_bool(value: str, default: bool = False) -> bool:
    return value.strip().lower() in {"true", "yes", "1"} if value else default


@dataclass(frozen=True)
class SkillDef:
    name: str
    description: str
    body: str
    #: False only for explicit workflow entry points. Set once, honoured by
    #: every target — this is the field whose per-tool drift caused the
    #: original template's Cursor and Claude configs to disagree.
    model_invocable: bool = True
    extras: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandDef:
    name: str
    description: str
    body: str


@dataclass(frozen=True)
class RuleDef:
    name: str
    description: str
    body: str
    globs: str = ""
    always_apply: bool = False


@dataclass(frozen=True)
class AgentDef:
    name: str
    description: str
    body: str
    tools: str = ""


@dataclass(frozen=True)
class McpServerDef:
    name: str
    command: str
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class HookDef:
    event: str
    matcher: str
    command: list[str]
    #: Marks hooks this tool owns, so re-rendering updates them without
    #: touching hooks a user added by hand.
    owner: str = "contextkeel"


@dataclass(frozen=True)
class TargetCapabilities:
    """What one editor can actually consume."""

    key: str
    glob_scoped_rules: bool
    nested_skills: bool
    per_skill_invocation_flag: bool
    supports_hooks: bool
    supports_agents: bool
    frontmatter_quotes_globs: bool


CAPABILITIES: dict[str, TargetCapabilities] = {
    "claude": TargetCapabilities(
        key="claude",
        glob_scoped_rules=False,
        nested_skills=True,
        per_skill_invocation_flag=True,
        supports_hooks=True,
        supports_agents=True,
        frontmatter_quotes_globs=False,
    ),
    "cursor": TargetCapabilities(
        key="cursor",
        glob_scoped_rules=True,
        nested_skills=True,
        per_skill_invocation_flag=True,
        supports_hooks=True,
        supports_agents=False,
        frontmatter_quotes_globs=False,
    ),
    "continue": TargetCapabilities(
        key="continue",
        glob_scoped_rules=True,
        nested_skills=False,
        per_skill_invocation_flag=False,
        supports_hooks=False,
        supports_agents=False,
        frontmatter_quotes_globs=True,
    ),
}


@dataclass
class ContentBundle:
    skills: list[SkillDef] = field(default_factory=list)
    commands: list[CommandDef] = field(default_factory=list)
    rules: list[RuleDef] = field(default_factory=list)
    agents: list[AgentDef] = field(default_factory=list)

    def skill(self, name: str) -> SkillDef | None:
        return next((s for s in self.skills if s.name == name), None)


def load_content(root: Path | None = None) -> ContentBundle:
    """Read the single canonical source shipped inside the package."""
    root = root or CONTENT_ROOT
    bundle = ContentBundle()

    skills_dir = root / "skills"
    if skills_dir.is_dir():
        extras: dict[str, dict[str, str]] = {}
        for path in sorted(skills_dir.glob("*.md")):
            # "<skill>.<extra>.md" is an auxiliary file belonging to a skill.
            stem_parts = path.stem.split(".")
            if len(stem_parts) > 1:
                extras.setdefault(stem_parts[0], {})[
                    ".".join(stem_parts[1:]) + ".md"
                ] = path.read_text(encoding="utf-8")
        for path in sorted(skills_dir.glob("*.md")):
            if len(path.stem.split(".")) > 1:
                continue
            meta, body = _split(path.read_text(encoding="utf-8"))
            name = meta.get("name", path.stem)
            bundle.skills.append(
                SkillDef(
                    name=name,
                    description=meta.get("description", ""),
                    body=body.strip() + "\n",
                    model_invocable=_as_bool(meta.get("model_invocable", "true"), True),
                    extras=extras.get(name, {}),
                )
            )

    for path in sorted((root / "commands").glob("*.md")):
        meta, body = _split(path.read_text(encoding="utf-8"))
        bundle.commands.append(
            CommandDef(
                name=meta.get("name", path.stem),
                description=meta.get("description", ""),
                body=body.strip() + "\n",
            )
        )

    for path in sorted((root / "rules").glob("*.md")):
        meta, body = _split(path.read_text(encoding="utf-8"))
        bundle.rules.append(
            RuleDef(
                name=meta.get("name", path.stem),
                description=meta.get("description", ""),
                body=body.strip() + "\n",
                globs=meta.get("globs", ""),
                always_apply=_as_bool(meta.get("always_apply", "false")),
            )
        )

    for path in sorted((root / "agents").glob("*.md")):
        meta, body = _split(path.read_text(encoding="utf-8"))
        bundle.agents.append(
            AgentDef(
                name=meta.get("name", path.stem),
                description=meta.get("description", ""),
                body=body.strip() + "\n",
                tools=meta.get("tools", ""),
            )
        )

    return bundle


__all__ = [
    "CAPABILITIES",
    "CONTENT_ROOT",
    "AgentDef",
    "CommandDef",
    "ContentBundle",
    "HookDef",
    "McpServerDef",
    "RuleDef",
    "SkillDef",
    "TargetCapabilities",
    "load_content",
]
