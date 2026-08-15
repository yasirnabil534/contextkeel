"""Shared fixtures.

Fixture repositories are built in ``tmp_path`` rather than checked in, so the
suite runs identically on Windows, macOS and Linux. Paths are always
constructed with ``pathlib`` — never by joining strings with ``/``.
"""

from __future__ import annotations

import contextlib
import json
import subprocess
from pathlib import Path

import pytest


def _git_init(path: Path) -> None:
    # git is not required for anything the tests assert.
    with contextlib.suppress(OSError, subprocess.CalledProcessError):
        subprocess.run(["git", "init", "-q"], cwd=path, check=True, capture_output=True)


@pytest.fixture
def node_repo(tmp_path: Path) -> Path:
    root = tmp_path / "node-app"
    (root / "src").mkdir(parents=True)
    (root / "package.json").write_text(
        json.dumps(
            {
                "name": "node-app",
                "dependencies": {"next": "14", "react": "18", "typescript": "5"},
                "devDependencies": {"vitest": "1", "tailwindcss": "3"},
            }
        ),
        encoding="utf-8",
    )
    (root / "pnpm-lock.yaml").write_text("", encoding="utf-8")
    (root / "src" / "app.ts").write_text(
        "import { helper } from './helper'\n"
        "export class Widget { render() { return helper() } }\n"
        "export function main() { return new Widget() }\n",
        encoding="utf-8",
    )
    (root / "src" / "helper.ts").write_text(
        "export function helper() { return 42 }\n", encoding="utf-8"
    )
    _git_init(root)
    return root


@pytest.fixture
def python_repo(tmp_path: Path) -> Path:
    root = tmp_path / "py-app"
    (root / "app").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "py-app"\ndependencies = ["fastapi", "sqlalchemy"]\n',
        encoding="utf-8",
    )
    (root / "uv.lock").write_text("", encoding="utf-8")
    (root / "app" / "main.py").write_text(
        "from app.service import compute\n\n\n"
        "class Server:\n    def start(self) -> int:\n        return compute()\n",
        encoding="utf-8",
    )
    (root / "app" / "service.py").write_text(
        "def compute() -> int:\n    return 7\n", encoding="utf-8"
    )
    _git_init(root)
    return root


@pytest.fixture
def go_repo(tmp_path: Path) -> Path:
    root = tmp_path / "go-app"
    root.mkdir(parents=True)
    (root / "go.mod").write_text(
        "module example.com/app\n\ngo 1.22\n", encoding="utf-8"
    )
    (root / "main.go").write_text(
        "package main\n\nfunc main() {}\n\nfunc helper() int { return 1 }\n",
        encoding="utf-8",
    )
    _git_init(root)
    return root


@pytest.fixture
def empty_repo(tmp_path: Path) -> Path:
    root = tmp_path / "empty"
    root.mkdir(parents=True)
    _git_init(root)
    return root


@pytest.fixture(autouse=True)
def _reset_console():
    """Each test starts in the default output register."""
    from contextkeel import console

    console.configure()
    yield
    console.configure()


@pytest.fixture(autouse=True)
def _no_viewer_installs(monkeypatch):
    """Never attempt to install a GUI application during tests."""
    from contextkeel.vault import viewer

    monkeypatch.setattr(viewer, "_install_command", lambda: None)


@pytest.fixture
def no_preferred_backend(monkeypatch):
    """Force the preferred indexer to look unavailable."""
    from contextkeel.graph import graphify_backend

    monkeypatch.setattr(
        graphify_backend.GraphifyBackend, "is_available", lambda self: False
    )
