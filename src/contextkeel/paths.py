"""Workspace discovery and path layout.

Everything is a :class:`pathlib.Path`; nothing here concatenates path strings.
Discovery never walks outside the user's tree.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

WORKSPACE_DIRNAME = ".contextkeel"
_ROOT_MARKERS = (".git", "project.yml", "pyproject.toml", "package.json", "go.mod")

GITIGNORE_BLOCK = """
# contextkeel workspace — generated locally, regenerated on demand.
.contextkeel/
graphify-out/
"""


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up for a repo marker, preferring ``.git``.

    Falls back to ``start`` itself so a bare directory still works — never
    returns a path above the user's starting point's filesystem root.
    """
    start = (start or Path.cwd()).resolve()
    if start.is_file():
        start = start.parent

    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    for candidate in (start, *start.parents):
        if any((candidate / marker).exists() for marker in _ROOT_MARKERS):
            return candidate
    return start


@dataclass(frozen=True)
class Layout:
    """Resolved locations for one workspace."""

    root: Path

    @property
    def workspace(self) -> Path:
        return self.root / WORKSPACE_DIRNAME

    @property
    def index(self) -> Path:
        return self.workspace / "index"

    @property
    def index_report(self) -> Path:
        return self.index / "REPORT.md"

    @property
    def index_json(self) -> Path:
        return self.index / "index.json"

    @property
    def state_file(self) -> Path:
        return self.workspace / "state.json"

    @property
    def logs(self) -> Path:
        return self.workspace / "logs"

    @property
    def docs(self) -> Path:
        return self.root / ".docs"

    def vault(self, name: str = "Vault") -> Path:
        return self.root / name

    def ensure(self) -> None:
        """Create the workspace directories. Idempotent."""
        for directory in (self.workspace, self.index, self.logs):
            directory.mkdir(parents=True, exist_ok=True)


def layout(start: Path | None = None) -> Layout:
    return Layout(root=find_repo_root(start))


def cache_dir() -> Path:
    """Per-user, per-OS cache location."""
    from platformdirs import user_cache_dir

    path = Path(user_cache_dir("contextkeel"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_gitignored(root: Path) -> bool:
    """Append the workspace dir to ``.gitignore``. Idempotent; never rewrites."""
    gitignore = root / ".gitignore"
    try:
        existing = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
        if WORKSPACE_DIRNAME in existing:
            return False
        with gitignore.open("a", encoding="utf-8") as fh:
            if existing and not existing.endswith("\n"):
                fh.write("\n")
            fh.write(GITIGNORE_BLOCK)
        return True
    except OSError:
        return False


__all__ = [
    "WORKSPACE_DIRNAME",
    "Layout",
    "cache_dir",
    "ensure_gitignored",
    "find_repo_root",
    "layout",
]
