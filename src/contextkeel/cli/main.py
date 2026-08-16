"""CLI application shell.

Imports stay lazy so ``ckeel --help`` remains fast — the indexer in particular
must not be imported to print usage.

One top-level exception handler maps errors to a single actionable line. A
stack trace never reaches the terminal in normal use; it goes to the log file,
where ``--verbose`` can point the developer at it.
"""

from __future__ import annotations

import contextlib
import logging
import sys
from pathlib import Path

import typer

from contextkeel.__about__ import __version__

app = typer.Typer(
    name="contextkeel",
    help="Keep any repository ready for AI agents, without thinking about it.",
    no_args_is_help=True,
    add_completion=False,
)

_STATE: dict[str, object] = {"root": None, "expert": False, "json": False}


def _configure(
    *, quiet: bool, json_mode: bool, expert_flag: bool, verbose: bool, root: Path | None
) -> None:
    from contextkeel import console, paths
    from contextkeel import expert as expert_mod

    is_expert = expert_mod.expert_enabled(
        flag=expert_flag, verbose=verbose, json_mode=json_mode
    )
    console.configure(quiet=quiet, json_mode=json_mode, expert=is_expert)
    _STATE["root"] = root
    _STATE["expert"] = is_expert
    _STATE["json"] = json_mode

    # Debug logging always records real tool names, to file only: stdout is
    # reserved for the active register (and, for the MCP server, the protocol).
    logger = logging.getLogger("contextkeel")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    try:
        layout = paths.layout(root)
        layout.logs.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(layout.logs / "contextkeel.log", encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(handler)
    except OSError:
        pass  # logging must never be the reason a command fails


@app.callback(invoke_without_command=True)
def main_callback(
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Only warnings and errors."
    ),
    json_mode: bool = typer.Option(False, "--json", help="Machine-readable output."),
    expert: bool = typer.Option(
        False, "--expert", help="Name every underlying tool and command."
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Debug logging."),
    root: Path | None = typer.Option(None, "--root", help="Override repo discovery."),
    version: bool = typer.Option(
        False, "--version", help="Print the version and exit."
    ),
) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit(0)
    _configure(
        quiet=quiet, json_mode=json_mode, expert_flag=expert, verbose=verbose, root=root
    )


def _root() -> Path | None:
    return _STATE["root"]  # type: ignore[return-value]


@app.command()
def init(
    auto: bool = typer.Option(
        False, "--auto", help="Non-interactive; pick every default."
    ),
    with_viewer: bool = typer.Option(
        False, "--with-viewer", help="Force the notes-viewer install."
    ),
    no_viewer: bool = typer.Option(False, "--no-viewer", help="Skip the notes viewer."),
    backend: str = typer.Option("", "--backend", help="Use a specific code indexer."),
    ci: bool = typer.Option(
        False, "--ci", help="Also add a CI check for stale context."
    ),
) -> None:
    """Set this repository up. Safe to run again at any time."""
    from contextkeel.cli import init as cmd

    raise typer.Exit(
        cmd.run(
            _root(),
            auto=auto,
            with_viewer=with_viewer,
            no_viewer=no_viewer,
            backend=backend,
            write_ci=ci,
        )
    )


@app.command()
def doctor(
    fix: bool = typer.Option(False, "--fix", help="Repair whatever can be repaired."),
) -> None:
    """Check this workspace and report anything wrong."""
    from contextkeel.cli import doctor as cmd

    raise typer.Exit(cmd.run(_root(), fix=fix, json_mode=bool(_STATE["json"])))


@app.command()
def sync(
    check: bool = typer.Option(
        False, "--check", help="Report staleness; write nothing."
    ),
    full: bool = typer.Option(False, "--full", help="Force a full rebuild."),
    backend: str = typer.Option("", "--backend", help="Use a specific code indexer."),
) -> None:
    """Refresh the code index and the project notes."""
    from contextkeel.cli import sync as cmd

    raise typer.Exit(cmd.run(_root(), check=check, full=full, backend=backend))


@app.command()
def status() -> None:
    """Where this project stands, in five lines."""
    from contextkeel.cli import status as cmd

    raise typer.Exit(cmd.run(_root(), json_mode=bool(_STATE["json"])))


@app.command()
def plan(
    requirements: str = typer.Argument(
        "", help="Requirements text, or a path to a file."
    ),
    tier: str = typer.Option("backend", "--tier", help="frontend | backend | mobile."),
    check: str = typer.Option("", "--check", help="Validate an existing plan file."),
    insert_after: str = typer.Option(
        "", "--insert-after", help="Allocate a retrofit code."
    ),
) -> None:
    """Turn requirements into a trackable, migration-style prompt plan."""
    from contextkeel.cli import plan as cmd

    text = requirements
    candidate = Path(requirements) if requirements else None
    if candidate and candidate.is_file():
        text = candidate.read_text(encoding="utf-8")

    raise typer.Exit(
        cmd.run(
            _root(),
            requirements=text,
            tier=tier,
            check=check,
            insert_after=insert_after,
        )
    )


@app.command()
def internals() -> None:
    """Name every underlying tool, command, and override. Hides nothing."""
    from contextkeel.cli import internals as cmd

    raise typer.Exit(cmd.run(_root(), json_mode=bool(_STATE["json"])))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def index(ctx: typer.Context) -> None:
    """Pass arguments straight through to the code indexer: `ckeel index -- --help`."""
    from contextkeel.cli import internals as cmd

    args = [a for a in ctx.args if a != "--"]
    raise typer.Exit(cmd.index_passthrough(_root(), args))


@app.command()
def upgrade(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Report without changing anything."
    ),
) -> None:
    """Update contextkeel itself."""
    from contextkeel import console
    from contextkeel.bootstrap import selfupdate

    result = selfupdate.upgrade(dry_run=dry_run)
    (console.ok if result.ok else console.fail)(result.detail)
    raise typer.Exit(0 if result.ok else 1)


@app.command(name="mcp-serve")
def mcp_serve(
    root: Path | None = typer.Option(None, "--root", help="Repository to serve."),
) -> None:
    """Run the MCP server (stdio). Editors start this for you."""
    from contextkeel.mcp.server import serve

    raise typer.Exit(serve(root or _root()))


@app.command(name="_hook", hidden=True)
def hook(name: str) -> None:
    """Internal hook entry point. Always exits 0."""
    from contextkeel.hooks.runner import run

    raise typer.Exit(run(name))


def main() -> int:
    """Console-script entry point with the top-level error handler."""
    from contextkeel.errors import ContextkeelError

    try:
        app(standalone_mode=False)
        return 0
    except typer.Exit as exc:
        return int(exc.exit_code)
    except ContextkeelError as exc:
        from contextkeel import console

        logging.getLogger("contextkeel").error(exc.detail, exc_info=exc)
        console.fail(exc.user_message)
        console.detail(exc.detail)
        return 1
    except KeyboardInterrupt:
        return 130
    except Exception as exc:  # noqa: BLE001 - no traceback in normal use
        from contextkeel import console, paths

        # Usage errors are click's to explain, and Typer vendors its own copy
        # of those classes — duck-type rather than import a specific one.
        if hasattr(exc, "show") and hasattr(exc, "exit_code"):
            exc.show()  # type: ignore[attr-defined]
            return int(exc.exit_code)  # type: ignore[attr-defined]

        logging.getLogger("contextkeel").exception("unexpected failure")
        # Name the error on the visible line. A log path is no help when the
        # machine that wrote it was a CI runner or a container that is gone.
        console.fail(f"Something unexpected went wrong: {type(exc).__name__}: {exc}")
        with contextlib.suppress(OSError):
            console.say(f"Details: {paths.layout().logs / 'contextkeel.log'}")
        console.detail(repr(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
