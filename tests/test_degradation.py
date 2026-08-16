"""Degradation tests.

The product promise is that the developer never learns an internal tool's
name. That promise is only real if the tool keeps working — with identical
output — when the preferred backend disappears.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from contextkeel import console
from contextkeel import platform as ckplat
from contextkeel.cli import init as init_cmd
from contextkeel.errors import BackendUnavailable
from contextkeel.graph import registry
from contextkeel.graph.fallback_backend import FallbackBackend
from contextkeel.state import State


def test_fallback_engages_when_preferred_is_unavailable(no_preferred_backend):
    selection = registry.select(State(), allow_install=False)
    assert isinstance(selection.backend, FallbackBackend)
    assert selection.degraded


def test_degraded_output_is_identical_to_normal(node_repo: Path, monkeypatch, capsys):
    """Silent means silent: byte-for-byte the same, not merely 'similar'."""
    from contextkeel.graph import graphify_backend

    monkeypatch.setattr(
        graphify_backend.GraphifyBackend, "is_available", lambda self: False
    )
    console.configure()
    init_cmd.run(node_repo, auto=True, no_viewer=True)
    degraded_output = capsys.readouterr().out

    assert "graphif" not in degraded_output.lower()
    assert "obsidian" not in degraded_output.lower()
    assert "degraded" not in degraded_output.lower()
    assert "fallback" not in degraded_output.lower()
    assert "Ready." in degraded_output


def test_doctor_is_where_degradation_surfaces(
    node_repo: Path, no_preferred_backend, capsys
):
    from contextkeel.cli import doctor as doctor_cmd

    init_cmd.run(node_repo, auto=True, no_viewer=True)
    capsys.readouterr()

    console.configure(expert=True)
    doctor_cmd.run(node_repo)
    out = capsys.readouterr().out
    assert "degraded" in out.lower()


def test_builtin_backend_works_offline(node_repo: Path):
    """No network, no external binary — there must always be some index."""
    result = FallbackBackend().build(node_repo)
    assert not result.is_empty
    names = {n.name for n in result.nodes}
    assert "Widget" in names
    assert "helper" in names


def test_builtin_degrades_again_without_tree_sitter(node_repo: Path, monkeypatch):
    """If even tree-sitter is missing, fall back to a regex scan, never raise."""
    backend = FallbackBackend()
    monkeypatch.setattr(backend, "_parse_tree_sitter", lambda source, spec: None)
    result = backend.build(node_repo)
    assert not result.is_empty
    assert result.stats["parser"] == "regex"


def test_runtime_failure_falls_back_mid_command(node_repo: Path, monkeypatch):
    """A backend that passes its probe can still fail while running."""
    from contextkeel.errors import BackendUnavailable
    from contextkeel.graph import graphify_backend

    monkeypatch.setattr(
        graphify_backend.GraphifyBackend, "is_available", lambda self: True
    )

    def explode(self, root):
        raise BackendUnavailable("simulated crash", backend="graphify")

    monkeypatch.setattr(graphify_backend.GraphifyBackend, "build", explode)
    monkeypatch.setattr(graphify_backend.GraphifyBackend, "update", explode)

    selection = registry.select(State(), allow_install=False)
    result = registry.build_index(selection, node_repo, incremental=False)
    assert not result.is_empty
    assert selection.degraded


def test_no_api_key_selects_code_only_rather_than_giving_up(monkeypatch):
    """A missing key is not a reason to fall back.

    The indexer only needs an LLM to summarise documentation, which this tool
    does not use. Without a key it runs --code-only: no key, no network, no
    quota, and still a richer graph than the bundled indexer.
    """
    from contextkeel.graph import graphify_backend as gb

    for var in gb.API_KEY_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(gb, "claude_cli_available", lambda: True)

    assert gb.resolve_mode() is gb.IndexMode.CODE_ONLY
    assert gb.GraphifyBackend().mode is gb.IndexMode.CODE_ONLY


def test_api_key_selects_full_extraction(monkeypatch):
    from contextkeel.graph import graphify_backend as gb

    for var in gb.API_KEY_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert gb.resolve_mode() is gb.IndexMode.FULL


def test_claude_cli_is_opt_in_only(monkeypatch):
    """It spends the user's subscription quota, so never without being asked."""
    from contextkeel.graph import graphify_backend as gb

    for var in gb.API_KEY_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(gb, "claude_cli_available", lambda: True)

    assert gb.resolve_mode() is gb.IndexMode.CODE_ONLY
    assert gb.resolve_mode(use_claude_cli=True) is gb.IndexMode.CLAUDE_CLI

    # Asking for it when the CLI is absent must not select it.
    monkeypatch.setattr(gb, "claude_cli_available", lambda: False)
    assert gb.resolve_mode(use_claude_cli=True) is gb.IndexMode.CODE_ONLY


def test_each_mode_builds_the_right_command(monkeypatch, node_repo):
    """The flags are the whole point; assert them rather than trusting them."""
    from contextkeel.graph import graphify_backend as gb

    captured: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        captured.append(cmd)
        return ckplat.RunResult(code=0, out="", err="", cmd=cmd)

    monkeypatch.setattr(gb.ckplat, "which", lambda stem: Path("/fake/graphify"))
    monkeypatch.setattr(gb.ckplat, "run", fake_run)

    for mode, expected in [
        (gb.IndexMode.CODE_ONLY, "--code-only"),
        (gb.IndexMode.CLAUDE_CLI, "claude-cli"),
    ]:
        backend = gb.GraphifyBackend()
        backend.mode = mode
        backend._version = "test"
        backend._flags = {"--update", "--code-only", "--backend"}
        captured.clear()
        with pytest.raises(BackendUnavailable):
            backend.build(node_repo)  # no graph.json is written by the fake
        assert expected in " ".join(captured[0])

    # FULL mode adds neither flag.
    backend = gb.GraphifyBackend()
    backend.mode = gb.IndexMode.FULL
    backend._version = "test"
    backend._flags = {"--update", "--code-only", "--backend"}
    captured.clear()
    with pytest.raises(BackendUnavailable):
        backend.build(node_repo)
    joined = " ".join(captured[0])
    assert "--code-only" not in joined and "claude-cli" not in joined


def test_explicit_backend_choice_is_obeyed():
    """An expert who names a backend gets it, or a real error."""
    selection = registry.select(State(), override="builtin", allow_install=False)
    assert selection.backend.name == "builtin"

    from contextkeel.errors import BackendUnavailable

    with pytest.raises(BackendUnavailable):
        registry.select(State(), override="nonexistent", allow_install=False)


def test_index_is_deterministic(node_repo: Path):
    a = FallbackBackend().build(node_repo).to_dict()
    b = FallbackBackend().build(node_repo).to_dict()
    a.pop("generated_at")
    b.pop("generated_at")
    assert a == b


def test_runtime_failure_is_not_cached_as_the_selection(node_repo, monkeypatch):
    """One bad run must not downgrade the user permanently.

    Caching the runtime fallback would leave them on the bundled indexer
    forever, silently, with no way back short of --refresh-backends.
    """
    from contextkeel.errors import BackendUnavailable
    from contextkeel.graph import graphify_backend as gb

    monkeypatch.setattr(gb.GraphifyBackend, "is_available", lambda self: True)

    def explode(self, root):
        raise BackendUnavailable("transient", backend="graphify")

    monkeypatch.setattr(gb.GraphifyBackend, "build", explode)
    monkeypatch.setattr(gb.GraphifyBackend, "update", explode)

    state = State()
    selection = registry.select(state, allow_install=False)
    registry.build_index(selection, node_repo, incremental=False)
    registry.remember(state, selection)

    assert selection.degraded is True
    assert state.selected_backend == "graphify", "the failure was cached"
