"""Optional notes viewer.

This is the module where "never bother the developer" is easiest to violate,
so the constraints are strict: it never prompts, never prints, never blocks,
and never fails the command it is part of. Its absence is not a warning — the
notes are plain markdown and work with no application at all.

It is also fully controllable, because a default should never become a
restriction: ``--with-viewer`` forces the attempt and reports failures
normally, ``--no-viewer`` skips it, and ``context.viewer`` pins the policy for
a whole project.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from contextkeel import platform as ckplat

log = logging.getLogger("contextkeel")

APP = "obsidian"
INSTALL_TIMEOUT = 90
DOWNLOAD_URL = "https://obsidian.md"

NOT_ATTEMPTED = "not-attempted"
INSTALLED = "yes"
FAILED = "no"


@dataclass(frozen=True)
class ViewerResult:
    status: str
    detail: str
    attempted: bool = False

    @property
    def ok(self) -> bool:
        return self.status == INSTALLED


def is_installed() -> bool:
    if ckplat.is_macos():
        return Path("/Applications/Obsidian.app").exists()
    if ckplat.is_windows():
        local = Path.home() / "AppData" / "Local" / "Obsidian"
        return local.exists() or ckplat.which("Obsidian") is not None
    return (
        ckplat.which("obsidian") is not None
        or Path("/var/lib/flatpak/app/md.obsidian.Obsidian").exists()
        or (Path.home() / ".local/share/flatpak/app/md.obsidian.Obsidian").exists()
    )


def ensure(
    *, policy: str = "auto", previous_status: str = NOT_ATTEMPTED, force: bool = False
) -> ViewerResult:
    """Best-effort install, governed by ``policy``.

    ``never`` skips entirely. ``always`` (or ``force``) attempts even in CI or
    headless environments and reports failures. ``auto`` attempts once, quietly,
    and gives up permanently on failure.
    """
    if policy == "never" and not force:
        return ViewerResult(NOT_ATTEMPTED, "disabled by configuration")

    if is_installed():
        return ViewerResult(INSTALLED, "already installed")

    insist = force or policy == "always"

    if not insist:
        if ckplat.is_headless():
            # Installing a GUI app in CI or on a headless box is pure waste.
            return ViewerResult(NOT_ATTEMPTED, "headless environment")
        if previous_status in {INSTALLED, FAILED}:
            # Attempted before; never retry on every command.
            return ViewerResult(previous_status, "previously attempted")

    cmd = _install_command()
    if cmd is None:
        return ViewerResult(
            FAILED, f"no supported installer here; see {DOWNLOAD_URL}", attempted=insist
        )

    log.debug("attempting viewer install: %s", " ".join(cmd))
    result = ckplat.run(cmd, timeout=INSTALL_TIMEOUT)

    if result.ok and is_installed():
        return ViewerResult(INSTALLED, "installed", attempted=True)
    if result.ok:
        return ViewerResult(INSTALLED, "installer reported success", attempted=True)
    return ViewerResult(
        FAILED,
        f"install failed ({result.code}); download manually from {DOWNLOAD_URL}",
        attempted=True,
    )


def _install_command() -> list[str] | None:
    """The right installer for this machine, or None if there isn't one.

    Linux desktop apps come from flatpak rather than the distro package
    manager, so probe for it directly instead of asking which apt/dnf/pacman
    is present.
    """
    if ckplat.is_macos() and ckplat.which("brew"):
        return ["brew", "install", "--cask", APP]
    if ckplat.is_windows() and ckplat.which("winget"):
        return [
            "winget",
            "install",
            "--id",
            "Obsidian.Obsidian",
            "--silent",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ]
    if ckplat.is_linux() and ckplat.which("flatpak"):
        return ["flatpak", "install", "-y", "flathub", "md.obsidian.Obsidian"]
    return None


__all__ = [
    "FAILED",
    "INSTALLED",
    "NOT_ATTEMPTED",
    "ViewerResult",
    "ensure",
    "is_installed",
]
