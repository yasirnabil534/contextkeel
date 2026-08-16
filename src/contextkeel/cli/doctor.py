"""``ckeel doctor`` — verify and self-repair.

The support surface: when something is wrong, this should be the only thing a
developer ever needs to run. ``--fix`` repairs everything repairable and never
destroys a hand-edited file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from contextkeel import console
from contextkeel.bootstrap import toolchain
from contextkeel.cli.common import open_workspace
from contextkeel.graph import registry, report
from contextkeel.hooks.payloads import default_hooks
from contextkeel.render import engine
from contextkeel.vault import scaffold, viewer

OK = "ok"
WARN = "warn"
FAIL = "fail"


@dataclass
class Check:
    name: str
    status: str
    detail: str
    hint: str = ""

    @property
    def symbol(self) -> str:
        return {OK: "✓", WARN: "!", FAIL: "✗"}[self.status]


def run(root: Path | None = None, *, fix: bool = False, json_mode: bool = False) -> int:
    workspace = open_workspace(root)
    checks: list[Check] = []

    # Toolchain --------------------------------------------------------------
    for name, result in toolchain.ensure_all(fix=fix).items():
        checks.append(
            Check(
                f"toolchain/{name}",
                OK if result.ok else FAIL,
                result.detail,
                "" if result.ok else "run `ckeel doctor --fix`",
            )
        )

    # Index backend ----------------------------------------------------------
    selection = registry.select(
        workspace.state,
        pinned=workspace.config.context.backend,
        allow_install=False,
        use_claude_cli=workspace.config.context.use_claude_cli,
    )
    checks.append(
        Check(
            "index/backend",
            OK,
            (
                "using the built-in indexer"
                if selection.degraded
                else "using the preferred indexer"
            ),
            "",
        )
    )
    console_detail = (
        f"backend={selection.backend.name} degraded={selection.degraded} "
        f"reason={selection.reason}"
    )

    # Index freshness --------------------------------------------------------
    existing = report.read(workspace.layout.index)
    if existing is None:
        if fix:
            from contextkeel.cli import sync as sync_cmd

            sync_cmd.run(workspace.root, full=True)
            checks.append(Check("index/freshness", OK, "rebuilt", ""))
        else:
            checks.append(
                Check("index/freshness", FAIL, "no index yet", "run `ckeel sync`")
            )
    else:
        checks.append(
            Check("index/freshness", OK, f"{len(existing.nodes)} entries", "")
        )

    # Config drift -----------------------------------------------------------
    known = {
        k: v
        for k, v in workspace.state.rendered_fingerprints.items()
        if not k.startswith("vault:")
    }
    render_report = engine.render(
        workspace.root,
        workspace.config,
        workspace.vault_dir,
        default_hooks(),
        known,
        check=not fix,
    )
    if render_report.conflicts:
        checks.append(
            Check(
                "editor/configs",
                WARN,
                f"{len(render_report.conflicts)} hand-edited: "
                + ", ".join(render_report.conflicts[:3]),
                "move the change into the source, or delete the file to regenerate it",
            )
        )
    elif render_report.changed and not fix:
        checks.append(
            Check(
                "editor/configs",
                WARN,
                f"{len(render_report.created) + len(render_report.updated)} out of date",
                "run `ckeel sync`",
            )
        )
    else:
        checks.append(Check("editor/configs", OK, "up to date", ""))
        if fix:
            for key, digest in render_report.fingerprints.items():
                workspace.state.rendered_fingerprints[key] = digest

    # Hooks ------------------------------------------------------------------
    settings = workspace.root / ".claude" / "settings.json"
    hooks_ok = settings.is_file() and "_hook" in settings.read_text(
        encoding="utf-8", errors="replace"
    )
    checks.append(
        Check(
            "hooks",
            OK if hooks_ok else WARN,
            "installed" if hooks_ok else "not installed",
            "" if hooks_ok else "run `ckeel doctor --fix`",
        )
    )

    # Notes ------------------------------------------------------------------
    if scaffold.is_scaffolded(workspace.vault_dir):
        checks.append(Check("notes", OK, str(workspace.vault_dir.name), ""))
    elif fix:
        scaffold.scaffold(workspace.vault_dir, workspace.config)
        checks.append(Check("notes", OK, "created", ""))
    else:
        checks.append(Check("notes", FAIL, "missing", "run `ckeel doctor --fix`"))

    # Optional viewer — informational only, never a warning -------------------
    checks.append(
        Check(
            "notes viewer (optional)",
            OK,
            "installed" if viewer.is_installed() else "not installed",
            "",
        )
    )

    if fix:
        workspace.save_state()

    if json_mode:
        console.emit_json(
            {
                "checks": [c.__dict__ for c in checks],
                "backend": {
                    "selected": selection.backend.name,
                    "degraded": selection.degraded,
                    "reason": selection.reason,
                },
            }
        )
    else:
        for check in checks:
            line = f"{check.symbol} {check.name}: {check.detail}"
            if check.hint and check.status != OK:
                line += f" → {check.hint}"
            console.say(line)
        console.detail(console_detail)

    return 1 if any(c.status == FAIL for c in checks) else 0


__all__ = ["Check", "run"]
