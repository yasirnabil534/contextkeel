"""Programmatic toolchain checks and repair.

The same logic as the shell installers, callable from Python, so that
``ckeel doctor --fix`` can repair a broken machine without the developer
having to find and re-run the installer. Behaviourally identical to
``bootstrap/install.sh`` and ``bootstrap/install.ps1`` — the end-to-end tests
assert the two agree on what "already installed" means.

Every function is idempotent and safe to call when nothing is wrong.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from contextkeel import platform as ckplat

UV_INSTALL_POSIX = "https://astral.sh/uv/install.sh"
UV_INSTALL_WINDOWS = "https://astral.sh/uv/install.ps1"
PYTHON_MIN = (3, 11)


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    detail: str
    fixed: bool = False

    @property
    def symbol(self) -> str:
        if self.fixed:
            return "repaired"
        return "ok" if self.ok else "missing"


def _version_tuple(text: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in text.strip().split():
        if chunk[:1].isdigit():
            for piece in chunk.split("."):
                digits = "".join(c for c in piece if c.isdigit())
                if not digits:
                    break
                parts.append(int(digits))
            if parts:
                break
    return tuple(parts)


def check_python(*, fix: bool = False) -> CheckResult:
    """The interpreter running this code is by definition present.

    ``ckeel`` is installed as an isolated tool with its own interpreter, so a
    stale or missing *system* Python is irrelevant to whether this works. Only
    report a problem if the running interpreter is somehow too old.
    """
    version = sys.version_info[:2]
    if version >= PYTHON_MIN:
        return CheckResult(True, f"Python {version[0]}.{version[1]}")
    return CheckResult(
        False,
        f"Python {version[0]}.{version[1]} is below the required "
        f"{PYTHON_MIN[0]}.{PYTHON_MIN[1]}",
    )


def check_uv(*, fix: bool = False) -> CheckResult:
    """``uv`` is how the tool installs and upgrades itself."""
    found = ckplat.which("uv")
    if found:
        result = ckplat.run([str(found), "--version"], timeout=20)
        return CheckResult(True, result.out.strip() or "uv present")

    if not fix:
        return CheckResult(False, "uv not installed")

    if ckplat.is_windows():
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"irm {UV_INSTALL_WINDOWS} | iex",
        ]
    else:
        cmd = ["sh", "-c", f"curl -LsSf {UV_INSTALL_POSIX} | sh"]

    result = ckplat.run(cmd, timeout=300)
    if not result.ok:
        return CheckResult(False, f"uv install failed: {result.output[:400]}")

    ckplat.ensure_on_path(ckplat.user_bin_dir())
    if ckplat.which("uv"):
        return CheckResult(True, "uv installed", fixed=True)
    return CheckResult(False, "uv installed but not on PATH")


def check_self_on_path(*, fix: bool = False) -> CheckResult:
    """Is the ``ckeel`` shim reachable from a fresh shell?"""
    if ckplat.which("ckeel"):
        return CheckResult(True, "ckeel on PATH")
    if not fix:
        return CheckResult(False, "ckeel is installed but not on PATH")
    added = ckplat.ensure_on_path(ckplat.user_bin_dir())
    if ckplat.which("ckeel"):
        return CheckResult(True, "PATH updated", fixed=added)
    return CheckResult(
        False,
        f"add {ckplat.user_bin_dir()} to PATH, or open a new terminal",
    )


def ensure_all(*, fix: bool = False) -> dict[str, CheckResult]:
    """Run every toolchain check. Order matters: uv underpins the rest."""
    return {
        "python": check_python(fix=fix),
        "uv": check_uv(fix=fix),
        "path": check_self_on_path(fix=fix),
    }


__all__ = [
    "PYTHON_MIN",
    "CheckResult",
    "check_python",
    "check_self_on_path",
    "check_uv",
    "ensure_all",
]
