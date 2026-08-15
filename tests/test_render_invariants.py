"""The regression net for the failures that motivated this project.

Each test here corresponds to something that actually went wrong in the
template contextkeel replaces.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from contextkeel import console
from contextkeel.cli import init as init_cmd
from contextkeel.cli.common import open_workspace
from contextkeel.hooks.payloads import default_hooks
from contextkeel.render import engine
from contextkeel.render.model import load_content


@pytest.fixture
def initialised(node_repo: Path, no_preferred_backend) -> Path:
    init_cmd.run(node_repo, auto=True, no_viewer=True)
    return node_repo


def generated_files(root: Path) -> dict[Path, str]:
    found: dict[Path, str] = {}
    for path in root.rglob("*"):
        if not path.is_file() or ".contextkeel" in path.parts or ".git" in path.parts:
            continue
        if any(
            p in path.parts for p in (".claude", ".cursor", ".continue")
        ) or path.name in {
            "AGENTS.md",
            ".mcp.json",
        }:
            found[path] = path.read_text(encoding="utf-8", errors="replace")
    return found


# -- Invariant 1: no foreign absolute paths --------------------------------


def test_no_foreign_absolute_paths(initialised: Path):
    """The bug: three MCP files hardcoded one developer's D:\\Learnings path."""
    offenders: list[str] = []
    pattern = re.compile(r"[A-Z]:\\\\[\w\\\\]+|/Users/[\w./-]+|/home/[\w./-]+")
    for path, text in generated_files(initialised).items():
        for match in pattern.finditer(text):
            if str(initialised) not in match.group(0):
                offenders.append(f"{path.name}: {match.group(0)}")
    assert not offenders, f"foreign absolute paths leaked: {offenders}"


def test_mcp_paths_resolve_inside_the_repo(initialised: Path):
    for rel in (".mcp.json", ".cursor/mcp.json", ".continue/mcpServers/mcp.json"):
        payload = json.loads((initialised / rel).read_text(encoding="utf-8"))
        for server in payload["mcpServers"].values():
            for arg in server["args"]:
                if arg.startswith(("/", "C:", "D:")):
                    assert str(initialised) in arg, f"{rel}: {arg} escapes the repo"


def test_all_three_mcp_files_agree(initialised: Path):
    """One function builds the dict; the three files cannot disagree."""
    payloads = [
        json.loads((initialised / rel).read_text(encoding="utf-8"))
        for rel in (".mcp.json", ".cursor/mcp.json", ".continue/mcpServers/mcp.json")
    ]
    assert payloads[0] == payloads[1] == payloads[2]


def test_relocating_the_repo_rewrites_paths(initialised: Path, tmp_path: Path):
    """Moving a repo used to leave every generated path pointing at the old one."""
    moved = tmp_path / "relocated"
    initialised.rename(moved)

    from contextkeel.cli import sync as sync_cmd

    sync_cmd.run(moved)
    payload = json.loads((moved / ".mcp.json").read_text(encoding="utf-8"))
    args = [a for s in payload["mcpServers"].values() for a in s["args"]]
    assert any(str(moved) in a for a in args)
    assert not any("initialised" in a for a in args)


# -- Invariant 2: the two registers, in both directions ---------------------


def test_default_register_hides_internal_names(initialised: Path, capsys):
    for path, text in generated_files(initialised).items():
        assert not re.search(r"graphif|obsidian", text, re.I), (
            f"{path.name} leaks a tool name"
        )

    from contextkeel.cli import doctor as doctor_cmd

    console.configure()
    doctor_cmd.run(initialised)
    out = capsys.readouterr().out
    assert not re.search(r"graphif|obsidian", out, re.I)


def test_expert_register_reveals_them(initialised: Path, capsys):
    """Hiding information from someone who asked is a bug too."""
    from contextkeel.cli import internals as internals_cmd

    console.configure(expert=True)
    internals_cmd.run(initialised)
    out = capsys.readouterr().out
    assert re.search(r"graphif", out, re.I), "expert mode must name the real backend"
    assert "obsidian" in out.lower(), "expert mode must name the notes viewer"


def test_json_output_is_always_the_expert_register(initialised: Path, capsys):
    from contextkeel.cli import status as status_cmd

    console.configure(json_mode=True)
    status_cmd.run(initialised, json_mode=True)
    payload = json.loads(capsys.readouterr().out)
    assert payload["index"]["backend"], "machine output must carry the real backend id"


def test_console_render_is_a_mapping_not_a_ban():
    console.configure()
    assert console.render("graphify") == "code index"
    console.configure(expert=True)
    assert console.render("graphify") == "graphify"


# -- Invariant 3: no unresolved template tokens in written notes ------------


def test_no_unresolved_tokens_in_notes(initialised: Path):
    """``Templates/`` legitimately keeps its tokens; nothing else may."""
    vault = initialised / "Vault"
    for path in vault.rglob("*.md"):
        if "Templates" in path.parts:
            continue
        assert "{{" not in path.read_text(encoding="utf-8"), (
            f"{path} has an unresolved token"
        )


def test_templates_keep_their_tokens(initialised: Path):
    templates = list((initialised / "Vault" / "Templates").glob("*.md"))
    assert templates
    assert all("{{" in p.read_text(encoding="utf-8") for p in templates)


# -- Invariant 4: no cross-tool references ---------------------------------


def test_continue_config_is_self_contained(initialised: Path):
    """Continue used to say "read .cursor/skills/..." and broke without it."""
    for path in (initialised / ".continue").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            assert ".cursor/" not in text, f"{path.name} references .cursor/"
            assert ".claude/" not in text, f"{path.name} references .claude/"


# -- Invariant 5: one invocation flag, honoured everywhere ------------------


def test_model_invocable_is_consistent_across_targets(initialised: Path):
    """Cursor had 14 skills flagged and Claude 2 — for no reason."""

    def flagged(directory: Path) -> set[str]:
        return {
            skill.parent.name
            for skill in directory.glob("*/SKILL.md")
            if "disable-model-invocation" in skill.read_text(encoding="utf-8")
        }

    claude = flagged(initialised / ".claude" / "skills")
    cursor = flagged(initialised / ".cursor" / "skills")
    assert claude == cursor, f"invocation flags drifted: {claude ^ cursor}"
    assert claude == {"load-context", "update-context"}


def test_every_skill_renders_to_every_target(initialised: Path):
    bundle = load_content()
    names = {s.name for s in bundle.skills}
    for target in (".claude", ".cursor"):
        rendered = {
            p.parent.name for p in (initialised / target / "skills").glob("*/SKILL.md")
        }
        assert rendered == names


# -- Idempotency and hand-edit safety --------------------------------------


def test_second_init_changes_nothing(initialised: Path):
    workspace = open_workspace(initialised)
    known = {
        k: v
        for k, v in workspace.state.rendered_fingerprints.items()
        if not k.startswith("vault:")
    }
    report = engine.render(
        initialised,
        workspace.config,
        workspace.vault_dir,
        default_hooks(),
        known,
        check=True,
    )
    assert not report.created and not report.updated, report.summary()


def test_hand_edited_files_are_preserved_and_reported(initialised: Path):
    target = initialised / ".claude" / "CLAUDE.md"
    target.write_text(
        target.read_text(encoding="utf-8") + "\n## Mine\nkeep me\n", encoding="utf-8"
    )

    init_cmd.run(initialised, auto=True, no_viewer=True)
    assert "keep me" in target.read_text(encoding="utf-8")

    workspace = open_workspace(initialised)
    known = {
        k: v
        for k, v in workspace.state.rendered_fingerprints.items()
        if not k.startswith("vault:")
    }
    report = engine.render(
        initialised,
        workspace.config,
        workspace.vault_dir,
        default_hooks(),
        known,
        check=True,
    )
    assert ".claude/CLAUDE.md" in report.conflicts


def test_user_permissions_and_hooks_survive_a_rerender(initialised: Path):
    settings_path = initialised / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings["permissions"]["allow"].append("Bash(my-own-tool:*)")
    settings.setdefault("hooks", {}).setdefault("PreToolUse", []).append(
        {"matcher": "*", "hooks": [{"type": "command", "command": "my-own-hook"}]}
    )
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")

    init_cmd.run(initialised, auto=True, no_viewer=True)

    merged = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "Bash(my-own-tool:*)" in merged["permissions"]["allow"]
    assert any(
        h["hooks"][0]["command"] == "my-own-hook"
        for h in merged["hooks"].get("PreToolUse", [])
    )
    assert "Bash(ckeel:*)" in merged["permissions"]["allow"]
