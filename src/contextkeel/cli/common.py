"""Shared workspace handle for the CLI and the MCP server.

Both surfaces delegate to the same functions, so there is no second
implementation to drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from contextkeel import config as config_mod
from contextkeel import paths as paths_mod
from contextkeel import state as state_mod


@dataclass
class Workspace:
    layout: paths_mod.Layout
    config: config_mod.Config
    state: state_mod.State

    @property
    def root(self) -> Path:
        return self.layout.root

    @property
    def vault_dir(self) -> Path:
        return self.layout.vault(self.config.context.vault)

    def save_state(self) -> None:
        state_mod.save(self.state, self.layout.state_file)


def open_workspace(root: Path | None = None, *, resolve: bool = True) -> Workspace:
    layout = paths_mod.layout(root)
    cfg = config_mod.load(layout.root)
    if resolve:
        cfg = config_mod.resolve(cfg, layout.root)
    state = state_mod.load(layout.state_file)
    return Workspace(layout=layout, config=cfg, state=state)


def git_sha(root: Path) -> str:
    from contextkeel import platform as ckplat

    result = ckplat.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, timeout=15)
    return result.out.strip() if result.ok else ""


__all__ = ["Workspace", "git_sha", "open_workspace"]
