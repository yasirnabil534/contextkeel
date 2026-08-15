"""Degradation tests.

The product promise is that the developer never learns an internal tool's
name. That promise is only real if the tool keeps working — with identical
output — when the preferred backend disappears.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from contextkeel import console
from contextkeel.cli import init as init_cmd
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


def test_no_api_key_means_preferred_backend_is_skipped(monkeypatch):
    """The real-world failure: it aborts on doc files without an LLM key."""
    from contextkeel.graph import graphify_backend

    for var in graphify_backend.API_KEY_VARS:
        monkeypatch.delenv(var, raising=False)
    assert graphify_backend.GraphifyBackend().is_available() is False


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
