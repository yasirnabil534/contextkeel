"""Expert mode — the counterpart to the neutral default register.

:mod:`contextkeel.console` keeps a developer from ever *needing* internal
knowledge. This module guarantees that anyone who *wants* it gets all of it:
real tool names, real versions, the exact commands run on their behalf, and
every override with its effective value and where that value came from.

Design rule: adding an escape hatch must never add a decision to the default
path. Someone who ignores everything here sees exactly the output they saw
before it existed.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from contextkeel import platform as ckplat
from contextkeel.__about__ import __version__

ENV_VAR = "CONTEXTKEEL_EXPERT"


def expert_enabled(
    *, flag: bool = False, verbose: bool = False, json_mode: bool = False
) -> bool:
    """Resolved once by the CLI and read everywhere else."""
    return bool(
        flag
        or verbose
        or json_mode
        or os.environ.get(ENV_VAR, "").strip().lower() in {"1", "true", "yes"}
    )


@dataclass
class Origin:
    """Where an effective value came from."""

    value: str
    source: str  # flag | project.yml | env | default


def collect(root: Path, cfg, state) -> dict:
    """Everything ``ckeel internals`` prints. Real names throughout."""
    from contextkeel import paths
    from contextkeel.console import INTERNAL_TERMS
    from contextkeel.graph import registry
    from contextkeel.vault import viewer

    layout = paths.Layout(root=root)
    backends = []
    for backend in registry.all_backends(allow_install=False):
        try:
            available = backend.is_available()
        except Exception as exc:  # noqa: BLE001
            available = f"probe error: {exc}"
        backends.append(
            {
                "name": backend.name,
                "priority": backend.priority,
                "available": available,
                "version": getattr(backend, "version", ""),
                "module": type(backend).__module__,
            }
        )

    from contextkeel.graph import graphify_backend as gb

    mode = gb.resolve_mode(use_claude_cli=cfg.context.use_claude_cli)
    pinned = cfg.context.backend
    return {
        "contextkeel": {
            "version": __version__,
            "executable": sys.argv[0],
            "python": sys.version.split()[0],
            "platform": str(ckplat.current_os()),
        },
        "workspace": {
            "root": str(root),
            "index": str(layout.index),
            "state": str(layout.state_file),
            "vault": str(layout.vault(cfg.context.vault)),
            "logs": str(layout.logs),
        },
        "index_backend": {
            "mode": str(mode),
            "why_this_mode": {
                gb.IndexMode.FULL: "an LLM API key is set, so documentation is summarised too",
                gb.IndexMode.CLAUDE_CLI: "opted in and the claude CLI is installed; uses your subscription quota",
                gb.IndexMode.CODE_ONLY: (
                    "no API key, so code is parsed locally and documentation is "
                    "skipped. No key, no network, no quota -- and this tool only "
                    "needs the code map anyway."
                ),
            }[mode],
            "api_key_set": gb.has_api_key(),
            "claude_cli_installed": gb.claude_cli_available(),
            "selected": state.selected_backend or "(not yet selected)",
            "degraded": state.backend_degraded,
            "reason": state.backend_reason,
            "probed_version": state.backend_probed_version,
            "candidates": backends,
        },
        "commands_run_on_your_behalf": _commands(),
        "notes_viewer": {
            "installed": viewer.is_installed(),
            "status": state.viewer_installed,
            "policy": Origin(
                cfg.context.viewer,
                "project.yml" if cfg.context.viewer != "auto" else "default",
            ).__dict__,
            "download": viewer.DOWNLOAD_URL,
        },
        "overrides": {
            "--backend": Origin(
                pinned or "(auto-select)",
                "project.yml" if pinned else "default",
            ).__dict__,
            "--with-viewer / --no-viewer": Origin(
                cfg.context.viewer, "project.yml"
            ).__dict__,
            "context.use_claude_cli": Origin(
                str(cfg.context.use_claude_cli),
                "project.yml" if cfg.context.use_claude_cli else "default",
            ).__dict__,
            "--expert": Origin(
                str(expert_enabled()),
                "env" if os.environ.get(ENV_VAR) else "default",
            ).__dict__,
        },
        # Closes the loop: any neutral phrase can be translated back.
        "vocabulary": {
            "note": (
                "The default register rewrites the left column to the right. "
                "Expert mode leaves text untouched."
            ),
            "mapping": dict(INTERNAL_TERMS),
        },
    }


def _commands() -> dict[str, str]:
    from contextkeel.graph import graphify_backend as gb

    return {
        "index (code-only, default)": f"{gb.CLI} . --code-only",
        "index (with an API key)": f"{gb.CLI} .",
        "index (via Claude CLI)": f"{gb.CLI} . --backend claude-cli",
        "index (install)": f"uv tool install {gb.PACKAGE}",
        "index (builtin fallback)": "in-process tree-sitter parse; no subprocess",
        "self-upgrade": "uv tool upgrade contextkeel",
        "notes viewer": "brew install --cask obsidian | winget install Obsidian.Obsidian "
        "| flatpak install flathub md.obsidian.Obsidian",
    }


def passthrough(root: Path, args: list[str]) -> int:
    """``ckeel index -- <args>`` — drive the real indexer directly."""
    from contextkeel.graph import graphify_backend as gb

    cli = ckplat.which(gb.CLI)
    if not cli:
        print(
            f"The preferred indexer ({gb.CLI}) is not installed. "
            f"Install it with: uv tool install {gb.PACKAGE}",
            file=sys.stderr,
        )
        return 1
    import subprocess

    return subprocess.call([str(cli), *args], cwd=str(root))  # noqa: S603


__all__ = ["ENV_VAR", "Origin", "collect", "expert_enabled", "passthrough"]
