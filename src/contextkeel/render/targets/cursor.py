"""Cursor target.

Cursor auto-applies ``.cursor/rules/*.mdc`` by file glob, so the language
idioms render as real rule files here. The frontmatter dialect differs from
Continue's (unquoted globs, ``alwaysApply``), which is exactly the kind of
per-tool shaping that belongs in a target and nowhere else.
"""

from __future__ import annotations

import json
from pathlib import Path

from contextkeel.render import mcp as mcp_render
from contextkeel.render.model import CAPABILITIES, ContentBundle, HookDef

CAPS = CAPABILITIES["cursor"]


def render(
    *,
    bundle: ContentBundle,
    root: Path,
    vault_dir: Path,
    hooks: list[HookDef],
    allowed_commands: list[str],
) -> dict[str, str]:
    files: dict[str, str] = {}

    for rule in bundle.rules:
        front = [f"description: {rule.description}"]
        if rule.globs:
            front.append(f"globs: {rule.globs}")
        front.append(f"alwaysApply: {str(rule.always_apply).lower()}")
        files[f".cursor/rules/{rule.name}.mdc"] = (
            "---\n" + "\n".join(front) + "\n---\n\n" + rule.body
        )

    for skill in bundle.skills:
        front = [f"name: {skill.name}", f"description: {skill.description}"]
        if CAPS.per_skill_invocation_flag and not skill.model_invocable:
            front.append("disable-model-invocation: true")
        files[f".cursor/skills/{skill.name}/SKILL.md"] = (
            "---\n" + "\n".join(front) + "\n---\n\n" + skill.body
        )
        for extra_name, extra_body in skill.extras.items():
            files[f".cursor/skills/{skill.name}/{extra_name}"] = extra_body

    for command in bundle.commands:
        files[f".cursor/commands/{command.name}.md"] = (
            f"# {command.description or command.name}\n\n{command.body}"
        )

    if CAPS.supports_hooks:
        files[".cursor/hooks.json"] = (
            json.dumps(
                {
                    "version": 1,
                    "hooks": {
                        "afterFileEdit": [
                            {"command": " ".join(h.command), "_owner": h.owner}
                            for h in hooks
                            if h.event in {"PostToolUse", "afterFileEdit"}
                        ]
                    },
                },
                indent=2,
            )
            + "\n"
        )

    files[".cursor/mcp.json"] = (
        json.dumps(mcp_render.build(root, vault_dir), indent=2) + "\n"
    )
    return files


__all__ = ["CAPS", "render"]
