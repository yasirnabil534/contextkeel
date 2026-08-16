"""Unit coverage for the foundation and the hook runner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from contextkeel import config as config_mod
from contextkeel import paths
from contextkeel import state as state_mod
from contextkeel.cli import plan as plan_cmd
from contextkeel.errors import BackendUnavailable, StateError
from contextkeel.hooks import runner
from contextkeel.vault import changelog, notes, scaffold

# -- config ----------------------------------------------------------------


def test_detects_node_stack(node_repo: Path):
    cfg = config_mod.resolve(config_mod.load(node_repo), node_repo)
    assert cfg.frontend.framework == "next"
    assert cfg.frontend.package_manager == "pnpm"
    assert cfg.frontend.styling == "tailwind"
    assert cfg.conventions.test_framework == "vitest"


def test_detects_python_stack(python_repo: Path):
    cfg = config_mod.resolve(config_mod.load(python_repo), python_repo)
    assert cfg.backend.language == "python"
    assert cfg.backend.framework == "fastapi"
    assert cfg.backend.package_manager == "uv"
    assert cfg.conventions.test_framework == "pytest"


def test_detects_go_stack(go_repo: Path):
    cfg = config_mod.resolve(config_mod.load(go_repo), go_repo)
    assert cfg.backend.language == "go"
    assert cfg.conventions.test_framework == "go-test"


def test_empty_repo_falls_back_to_defaults(empty_repo: Path):
    cfg = config_mod.resolve(config_mod.load(empty_repo), empty_repo)
    assert cfg.frontend.framework == "react"
    assert cfg.backend.framework == "express"


def test_malformed_config_never_blocks(tmp_path: Path):
    """Blocking a developer on config is the one thing this must not do."""
    (tmp_path / "project.yml").write_text("{{{ not yaml", encoding="utf-8")
    cfg = config_mod.load(tmp_path)
    assert cfg.defaults


def test_save_preserves_comments(tmp_path: Path):
    (tmp_path / "project.yml").write_text(
        "# a meaningful comment\nproject:\n  name: demo\n", encoding="utf-8"
    )
    cfg = config_mod.load(tmp_path)
    cfg.project.description = "set by a test"
    config_mod.save(cfg, tmp_path)
    assert "# a meaningful comment" in (tmp_path / "project.yml").read_text(
        encoding="utf-8"
    )


# -- paths and state -------------------------------------------------------


def test_repo_root_found_from_a_nested_directory(node_repo: Path):
    nested = node_repo / "src"
    assert paths.find_repo_root(nested) == node_repo


def test_gitignore_append_is_idempotent(node_repo: Path):
    assert paths.ensure_gitignored(node_repo) is True
    assert paths.ensure_gitignored(node_repo) is False
    assert (node_repo / ".gitignore").read_text(encoding="utf-8").count(
        ".contextkeel/"
    ) == 1


def test_corrupt_state_degrades_to_defaults(tmp_path: Path):
    path = tmp_path / "state.json"
    path.write_text("{ not json", encoding="utf-8")
    assert state_mod.load(path).selected_backend == ""
    assert path.with_suffix(".json.bak").is_file()


def test_future_schema_is_an_error(tmp_path: Path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"schema_version": 999}), encoding="utf-8")
    with pytest.raises(StateError):
        state_mod.load(path)


# -- errors ----------------------------------------------------------------


def test_errors_keep_detail_but_neutralise_the_message():
    exc = BackendUnavailable("graphify 0.9 exited 1", backend="graphify")
    assert "graphify" in exc.detail
    assert "graphify" not in exc.user_message


# -- vault -----------------------------------------------------------------


def test_notes_merge_preserves_user_sections(tmp_path: Path):
    path = tmp_path / "note.md"
    path.write_text(
        "---\na: 1\n---\n\n## One\nbody\n\n## Mine\nkeep me\n", encoding="utf-8"
    )
    note = notes.load(path)
    notes.upsert_section(note, "One", "replaced")
    notes.save(note, path)
    text = path.read_text(encoding="utf-8")
    assert "keep me" in text
    assert "replaced" in text
    assert "a: 1" in text


def test_note_roundtrip_is_lossless(tmp_path: Path):
    original = "---\nx: 1\n---\n\nintro\n\n## A\nbody a\n\n## B\nbody b\n"
    path = tmp_path / "n.md"
    path.write_text(original, encoding="utf-8")
    notes.save(notes.load(path), path)
    assert path.read_text(encoding="utf-8") == original


def test_changelog_is_newest_first(tmp_path: Path):
    path = tmp_path / "Changelog.md"
    changelog.prepend_entry(path, "First", "Did a thing.")
    changelog.prepend_entry(path, "Second", "Did another thing.")
    lines = path.read_text(encoding="utf-8").splitlines()
    headings = [line for line in lines if line.startswith("## ")]
    assert "Second" in headings[0]


def test_changelog_rejects_machine_prose(tmp_path: Path):
    path = tmp_path / "Changelog.md"
    with pytest.raises(changelog.ChangelogError):
        changelog.prepend_entry(path, "Bad", "Edited src/app/main.py and friends.")


def test_adr_numbering_handles_gaps(tmp_path: Path):
    decisions = tmp_path / "Decisions"
    decisions.mkdir()
    (decisions / "0001-a.md").write_text("x", encoding="utf-8")
    (decisions / "0007-b.md").write_text("x", encoding="utf-8")
    assert changelog.next_adr_number(decisions) == 8


def test_scaffold_is_idempotent(tmp_path: Path, empty_repo: Path):
    cfg = config_mod.resolve(config_mod.load(empty_repo), empty_repo)
    vault = tmp_path / "Vault"
    first = scaffold.scaffold(vault, cfg)
    second = scaffold.scaffold(vault, cfg, first.fingerprints)
    assert first.created
    assert not second.changed


# -- hooks: the rules that matter ------------------------------------------


def test_hook_always_exits_zero_even_when_the_handler_raises(monkeypatch, capsys):
    def explode(payload):
        raise RuntimeError("boom")

    monkeypatch.setitem(runner.HANDLERS, "tidy", explode)
    monkeypatch.setattr(runner, "_read_stdin", lambda: {})
    assert runner.run("tidy") == 0
    assert capsys.readouterr().out == "{}"


def test_hook_exits_zero_for_an_unknown_name(monkeypatch, capsys):
    monkeypatch.setattr(runner, "_read_stdin", lambda: {})
    assert runner.run("no-such-hook") == 0
    assert capsys.readouterr().out == "{}"


def test_hook_reads_both_payload_shapes():
    nested = {"tool_input": {"file_path": "/x/a.md"}}
    flat = {"file_path": "/x/a.md"}
    assert runner._file_path_from(nested) == Path("/x/a.md")
    assert runner._file_path_from(flat) == Path("/x/a.md")


def test_tidy_normalises_markdown(tmp_path: Path):
    path = tmp_path / "note.md"
    path.write_text("a   \n\n\n\nb\n\n\n", encoding="utf-8")
    runner.tidy_markdown({"file_path": str(path)})
    assert path.read_text(encoding="utf-8") == "a\n\nb\n"


def test_sync_hook_is_debounced(node_repo: Path, no_preferred_backend):
    from contextkeel.cli import init as init_cmd

    init_cmd.run(node_repo, auto=True, no_viewer=True)
    layout = paths.layout(node_repo)
    current = state_mod.load(layout.state_file)
    current.touch_hook()
    state_mod.save(current, layout.state_file)

    before = layout.index_json.stat().st_mtime_ns
    runner.sync_index({"file_path": str(node_repo / "src" / "app.ts")})
    assert layout.index_json.stat().st_mtime_ns == before, (
        "debounce did not suppress the run"
    )


# -- plan format -----------------------------------------------------------


def test_plan_boxes_are_aligned():
    entry = plan_cmd.PromptEntry(
        code="CK-0001",
        scope="S1",
        scope_name="Foundation",
        title="A title",
        files=["a/b.py"],
        critical=True,
    )
    lines = plan_cmd.render_box(entry).splitlines()
    assert len({len(line) for line in lines}) == 1


def test_plan_validates_and_catches_broken_pointers():
    entries = [
        plan_cmd.PromptEntry(
            code="CK-0000", scope="S0", scope_name="Setup", title="Setup"
        ),
        plan_cmd.PromptEntry(
            code="CK-0001", scope="S1", scope_name="Build", title="Build"
        ),
    ]
    text = plan_cmd.render_plan("demo", "backend", entries)
    assert plan_cmd.validate(text) == []
    assert plan_cmd.validate(
        text.replace("NEXT       : CK-0001", "NEXT       : CK-9999")
    )


def test_retrofit_codes_use_letter_suffixes():
    entries = [
        plan_cmd.PromptEntry(code="CK-0009", scope="S1", scope_name="Build", title="x")
    ]
    text = plan_cmd.render_plan("demo", "backend", entries)
    assert plan_cmd.next_retrofit_code(text, "CK-0009") == "CK-0009A"


# -- tier inference --------------------------------------------------------


def test_python_cli_is_not_given_a_phantom_frontend(python_repo: Path):
    """The 'works with nothing configured' rule must not invent tiers."""
    cfg = config_mod.resolve(config_mod.load(python_repo), python_repo)
    assert cfg.project.type == "backend"
    assert not cfg.has_frontend
    assert cfg.backend.language == "python"
    # The defaults block describes a TypeScript/Express stack; it must not be
    # layered on top of a detected Python one.
    assert cfg.backend.framework != "express"
    assert cfg.backend.runtime != "node"


def test_go_repo_is_backend_only(go_repo: Path):
    cfg = config_mod.resolve(config_mod.load(go_repo), go_repo)
    assert cfg.project.type == "backend"
    assert cfg.backend.language == "go"


def test_node_app_with_a_frontend_stays_fullstack(node_repo: Path):
    cfg = config_mod.resolve(config_mod.load(node_repo), node_repo)
    assert cfg.has_frontend
    assert cfg.frontend.framework == "next"


def test_empty_repo_still_gets_a_working_default(empty_repo: Path):
    cfg = config_mod.resolve(config_mod.load(empty_repo), empty_repo)
    assert cfg.project.type == "fullstack"
    assert cfg.frontend.framework == "react"


# -- console encoding ------------------------------------------------------


def test_output_survives_a_cp1252_stream(monkeypatch):
    """Windows consoles default to cp1252 and cannot encode the arrow glyph.

    This crashed `ckeel init` on Windows with UnicodeEncodeError. Streams that
    can be switched to UTF-8 are; this covers the ones that cannot, which is
    the case that actually broke.
    """
    import io
    import sys as _sys

    from contextkeel import console

    class Cp1252Stream(io.StringIO):
        """No reconfigure(), so the UTF-8 upgrade cannot rescue it."""

        encoding = "cp1252"

    stream = Cp1252Stream()
    console.configure()
    monkeypatch.setattr(_sys, "stdout", stream)

    console.step("Setting up demo")
    console.ok("done")

    written = stream.getvalue()
    assert "-> Setting up demo" in written
    assert "OK done" in written
    assert "\u2192" not in written and "\u2713" not in written
    # And it must be genuinely encodable on such a console.
    written.encode("cp1252")
