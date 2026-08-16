"""``ckeel sync`` — keep the context true.

Called by the stop hook, by CI, and occasionally by hand. Quiet under the hook
path; a two-line summary when a human runs it.
"""

from __future__ import annotations

from pathlib import Path

from contextkeel import console
from contextkeel.cli.common import git_sha, open_workspace
from contextkeel.errors import BackendUnavailable
from contextkeel.graph import registry, report
from contextkeel.hooks.payloads import default_hooks
from contextkeel.render import engine
from contextkeel.vault import notes as notes_mod
from contextkeel.vault import scaffold


def run(
    root: Path | None = None,
    *,
    check: bool = False,
    full: bool = False,
    backend: str = "",
) -> int:
    workspace = open_workspace(root)
    workspace.layout.ensure()
    stale: list[str] = []

    # 1. Index ---------------------------------------------------------------
    try:
        selection = registry.select(
            workspace.state,
            override=backend,
            pinned=workspace.config.context.backend,
            refresh=bool(backend),
            use_claude_cli=workspace.config.context.use_claude_cli,
        )
        if check:
            existing = report.read(workspace.layout.index)
            if existing is None:
                stale.append("code index is missing")
        else:
            result = registry.build_index(
                selection, workspace.root, incremental=not full
            )
            report.write(result, workspace.layout.index)
            registry.remember(workspace.state, selection)
            console.say(
                f"Indexed {result.stats.get('files', len(result.nodes))} files."
            )
            console.detail(
                f"backend={selection.backend.name} degraded={selection.degraded}"
            )
    except BackendUnavailable as exc:
        console.detail(f"index failed: {exc.detail}")
        if check:
            stale.append("code index could not be built")

    # 2. Derived notes -------------------------------------------------------
    known_notes = {
        k[len("vault:") :]: v
        for k, v in workspace.state.rendered_fingerprints.items()
        if k.startswith("vault:")
    }
    if not check:
        scaffold_result = scaffold.scaffold(
            workspace.vault_dir, workspace.config, known_notes
        )
        for key, digest in scaffold_result.fingerprints.items():
            workspace.state.rendered_fingerprints[f"vault:{key}"] = digest
        _refresh_tech_stack(workspace)

    # 3. Agent configs -------------------------------------------------------
    render_report = engine.render(
        workspace.root,
        workspace.config,
        workspace.vault_dir,
        default_hooks(),
        {
            k: v
            for k, v in workspace.state.rendered_fingerprints.items()
            if not k.startswith("vault:")
        },
        check=check,
    )
    if check and render_report.changed:
        stale.append(
            f"editor configs are out of date ({len(render_report.created) + len(render_report.updated)} files)"
        )
    if not check:
        for key, digest in render_report.fingerprints.items():
            workspace.state.rendered_fingerprints[key] = digest
        console.say(f"Editor setup: {render_report.summary()}")
        if render_report.conflicts:
            console.warn(
                f"{len(render_report.conflicts)} generated file(s) were edited by hand "
                "and left untouched — run `ckeel doctor` to see which."
            )

    if check:
        if stale:
            for item in stale:
                console.fail(item)
            return 1
        console.ok("Context is up to date.")
        return 0

    workspace.state.touch_sync(git_sha(workspace.root))
    workspace.save_state()
    return 0


def _refresh_tech_stack(workspace) -> None:
    """Tech Stack is derived, so keep it true without touching authored notes."""
    path = workspace.vault_dir / "Context" / "Tech Stack.md"
    if not path.is_file():
        return
    from contextkeel.config import summary

    note = notes_mod.load(path)
    notes_mod.upsert_section(note, "Summary", summary(workspace.config))
    notes_mod.save(note, path)


__all__ = ["run"]
