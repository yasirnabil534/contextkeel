"""Cross-platform primitives.

Every operating-system difference in this package lives here. Code elsewhere
that branches on the OS is a bug — it means a platform-specific assumption has
escaped into logic that is supposed to be portable.

macOS, Windows and Linux are equal targets.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

DEFAULT_TIMEOUT = 120


class OS(StrEnum):
    MACOS = "macos"
    WINDOWS = "windows"
    LINUX = "linux"


def current_os() -> OS:
    if sys.platform == "darwin":
        return OS.MACOS
    if sys.platform in {"win32", "cygwin"}:
        return OS.WINDOWS
    return OS.LINUX


def is_windows() -> bool:
    return current_os() is OS.WINDOWS


def is_macos() -> bool:
    return current_os() is OS.MACOS


def is_linux() -> bool:
    return current_os() is OS.LINUX


def is_headless() -> bool:
    """True when there is no desktop session to install a GUI app into.

    Also true in CI, where installing a graphical application is pure waste.
    """
    if os.environ.get("CI"):
        return True
    if current_os() is OS.LINUX:
        return not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return False


def executable_name(stem: str) -> str:
    """``ckeel`` -> ``ckeel.exe`` on Windows."""
    return f"{stem}.exe" if is_windows() else stem


def user_bin_dir() -> Path:
    """Where ``uv tool install`` places its shims."""
    if is_windows():
        return Path(os.environ.get("USERPROFILE", Path.home())) / ".local" / "bin"
    return Path.home() / ".local" / "bin"


def which(stem: str) -> Path | None:
    """Locate an executable, including one only present in the user bin dir.

    A freshly installed shim is often not yet on the inherited PATH of the
    running process, so fall back to an explicit look in ``user_bin_dir()``.
    """
    found = shutil.which(stem)
    if found:
        return Path(found)
    candidate = user_bin_dir() / executable_name(stem)
    return candidate if candidate.is_file() else None


@dataclass(frozen=True)
class RunResult:
    """Outcome of a subprocess call."""

    code: int
    out: str
    err: str
    cmd: list[str]
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.code == 0 and not self.timed_out

    @property
    def output(self) -> str:
        """Combined streams, for diagnostics."""
        return (self.out + ("\n" if self.out and self.err else "") + self.err).strip()


def run(
    cmd: list[str],
    *,
    timeout: int = DEFAULT_TIMEOUT,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = False,
) -> RunResult:
    """The only subprocess wrapper in this package.

    Forces UTF-8 decoding with replacement: Windows consoles default to cp1252
    and raise ``UnicodeDecodeError`` on tool output that contains anything
    outside it. Never uses ``shell=True``; always passes an argument list;
    always sets a timeout.
    """
    merged_env = {**os.environ, **(env or {})}
    try:
        proc = subprocess.run(  # noqa: S603 - argument list, never shell
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=str(cwd) if cwd else None,
            env=merged_env,
            check=False,
        )
    except FileNotFoundError:
        return RunResult(code=127, out="", err=f"not found: {cmd[0]}", cmd=cmd)
    except subprocess.TimeoutExpired:
        return RunResult(
            code=124, out="", err=f"timed out after {timeout}s", cmd=cmd, timed_out=True
        )

    result = RunResult(
        code=proc.returncode, out=proc.stdout or "", err=proc.stderr or "", cmd=cmd
    )
    if check and not result.ok:
        from contextkeel.errors import ToolchainError

        raise ToolchainError(
            f"command failed ({result.code}): {' '.join(cmd)}\n{result.output}"
        )
    return result


def ensure_on_path(directory: Path) -> bool:
    """Persistently add ``directory`` to the user's PATH.

    Idempotent: returns False when the entry is already present. Uses ``setx``
    on Windows and the appropriate shell rc file on POSIX.
    """
    directory = directory.expanduser()
    entries = os.environ.get("PATH", "").split(os.pathsep)
    if str(directory) in entries:
        return False

    if is_windows():
        current = os.environ.get("PATH", "")
        run(["setx", "PATH", f"{current}{os.pathsep}{directory}"], timeout=30)
    else:
        line = f'\nexport PATH="{directory}:$PATH"\n'
        for rc in _posix_rc_files():
            try:
                existing = rc.read_text(encoding="utf-8") if rc.is_file() else ""
                if str(directory) in existing:
                    continue
                rc.parent.mkdir(parents=True, exist_ok=True)
                with rc.open("a", encoding="utf-8") as fh:
                    fh.write(line)
            except OSError:
                continue

    # Patch the running process too, so the caller can use it immediately.
    os.environ["PATH"] = f"{os.environ.get('PATH', '')}{os.pathsep}{directory}"
    return True


def _posix_rc_files() -> list[Path]:
    home = Path.home()
    shell = Path(os.environ.get("SHELL", "/bin/sh")).name
    if shell == "zsh":
        return [home / ".zshrc"]
    if shell == "fish":
        return [home / ".config" / "fish" / "config.fish"]
    return [home / ".bashrc", home / ".profile"]


def package_manager() -> str | None:
    """The system package manager available on this machine, if any."""
    candidates = {
        OS.MACOS: ["brew"],
        OS.WINDOWS: ["winget"],
        OS.LINUX: ["apt-get", "dnf", "pacman", "zypper"],
    }[current_os()]
    for name in candidates:
        if shutil.which(name):
            return name
    return None


__all__ = [
    "DEFAULT_TIMEOUT",
    "OS",
    "RunResult",
    "current_os",
    "ensure_on_path",
    "executable_name",
    "is_headless",
    "is_linux",
    "is_macos",
    "is_windows",
    "package_manager",
    "run",
    "user_bin_dir",
    "which",
]
