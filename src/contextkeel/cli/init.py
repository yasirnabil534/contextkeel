"""``ckeel init`` — the only command most developers will ever type.

Everything it needs is inferred; nothing is asked. Partial failure never
aborts the run: if the index cannot be built, the configs and notes are still
written and ``doctor`` reports the gap. Total output stays under eight lines.
"""

from __future__ import annotations

import logging
from pathlib import Path

from contextkeel import config as config_mod
from contextkeel import console
from contextkeel import paths as paths_mod
from contextkeel.cli.common import Workspace, git_sha, open_workspace
from contextkeel.errors import BackendUnavailable
from contextkeel.graph import registry, report
from contextkeel.hooks.payloads import default_hooks
from contextkeel.render import engine
from contextkeel.vault import scaffold, viewer

log = logging.getLogger("contextkeel")


def run(
    root: Path | None = None,
    *,
    auto: bool = False,
    with_viewer: bool = False,
    no_viewer: bool = False,
    backend: str = "",
    write_ci: bool = False,
) -> int:
    workspace = open_workspace(root)
    layout = workspace.layout
    layout.ensure()
    paths_mod.ensure_gitignored(layout.root)

    console.step(f"Setting up {layout.root.name}")

    # 1. Stack ---------------------------------------------------------------
    resolved = workspace.config
    if not (layout.root / "project.yml").is_file():
        config_mod.save(resolved, layout.root)
    console.say(f"  Stack: {config_mod.summary(resolved)}")

    # 2. Notes ---------------------------------------------------------------
    known_notes = {
        k[len("vault:") :]: v
        for k, v in workspace.state.rendered_fingerprints.items()
        if k.startswith("vault:")
    }
    notes = scaffold.scaffold(workspace.vault_dir, resolved, known_notes)
    for key, digest in notes.fingerprints.items():
        workspace.state.rendered_fingerprints[f"vault:{key}"] = digest

    # 3. Agent configs and hooks --------------------------------------------
    render_report = engine.render(
        layout.root,
        resolved,
        workspace.vault_dir,
        default_hooks(),
        {
            k: v
            for k, v in workspace.state.rendered_fingerprints.items()
            if not k.startswith("vault:")
        },
    )
    for key, digest in render_report.fingerprints.items():
        workspace.state.rendered_fingerprints[key] = digest
    console.say(f"  Editor setup: {render_report.summary()}")

    # 4. Index ---------------------------------------------------------------
    indexed = _build_index(workspace, backend)

    # 5. Optional viewer -----------------------------------------------------
    policy = resolved.context.viewer
    if no_viewer:
        policy = "never"
    result = viewer.ensure(
        policy=policy,
        previous_status=workspace.state.viewer_installed,
        force=with_viewer,
    )
    workspace.state.viewer_installed = result.status
    if with_viewer and not result.ok:
        console.warn(f"Notes viewer: {result.detail}")

    # 6. Optional CI ---------------------------------------------------------
    if write_ci:
        _write_ci(layout.root)
        console.say("  Added a CI check for stale context.")

    workspace.state.contextkeel_version = _version()
    workspace.state.touch_sync(git_sha(layout.root))
    workspace.save_state()

    if indexed:
        console.ok("Ready. Your editor already knows this project.")
    else:
        console.ok("Ready. Run `ckeel doctor` to finish indexing.")
    return 0


def _build_index(workspace: Workspace, backend: str) -> bool:
    try:
        selection = registry.select(
            workspace.state,
            override=backend,
            pinned=workspace.config.context.backend,
            refresh=bool(backend),
        )
        result = registry.build_index(selection, workspace.root, incremental=False)
        report.write(result, workspace.layout.index)
        registry.remember(workspace.state, selection)
        files = result.stats.get("files", len(result.nodes))
        console.say(f"  Indexed {files} files.")
        console.detail(
            f"  backend={selection.backend.name} degraded={selection.degraded} "
            f"reason={selection.reason}"
        )
        return True
    except BackendUnavailable as exc:
        # Never abort init for this: the rest of the workspace is still useful.
        log.warning("index build failed: %s", exc.detail)
        console.detail(f"  index failed: {exc.detail}")
        return False


def _write_ci(root: Path) -> None:
    source = Path(__file__).parent.parent / "templates" / "ci-drift-check.yml"
    if not source.is_file():
        return
    target = root / ".github" / "workflows" / "contextkeel.yml"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def _version() -> str:
    from contextkeel.__about__ import __version__

    return __version__


__all__ = ["run"]
