"""Exception hierarchy.

Every error carries two messages:

* ``str(exc)`` — full developer-facing detail, including real tool names,
  versions and failing command lines. Always complete, always logged.
* ``user_message`` — short, actionable, and written for the default output
  register (see :mod:`contextkeel.console`).

The split is what lets the CLI stay quiet for a developer who does not care
how the internals work while losing nothing for one who does: expert mode
surfaces the full detail verbatim.
"""

from __future__ import annotations

_GENERIC = "Something went wrong. Run `ckeel doctor` to check this workspace."


class ContextkeelError(Exception):
    """Base class for every error this package raises deliberately."""

    #: Fallback shown when a subclass does not supply its own.
    default_user_message: str = _GENERIC

    def __init__(self, detail: str, *, user_message: str | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self._user_message = user_message

    @property
    def user_message(self) -> str:
        """Short, neutral, actionable. Never empty."""
        return self._user_message or self.default_user_message


class ToolchainError(ContextkeelError):
    """Python, uv, or the ``ckeel`` shim itself is missing or unusable."""

    default_user_message = (
        "Required tooling is missing. Run `ckeel doctor --fix` to repair it."
    )


class BackendUnavailable(ContextkeelError):
    """A code-index backend cannot run.

    The neutral ``user_message`` deliberately omits the backend name; the full
    detail (name, version, failing command) always stays on ``detail`` and is
    printed verbatim in expert mode. Degrade silently, never opaquely.
    """

    default_user_message = "The code index could not be built right now."

    def __init__(
        self,
        detail: str,
        *,
        backend: str = "unknown",
        user_message: str | None = None,
    ) -> None:
        super().__init__(detail, user_message=user_message)
        self.backend = backend


class RenderConflict(ContextkeelError):
    """A generated file was hand-edited and would be clobbered by a re-render."""

    default_user_message = (
        "Some generated files were edited by hand and were left untouched. "
        "Run `ckeel doctor` to see which."
    )

    def __init__(self, detail: str, *, paths: list[str] | None = None) -> None:
        super().__init__(detail)
        self.paths = paths or []


class VaultError(ContextkeelError):
    """The notes tree is missing or malformed."""

    default_user_message = (
        "The project notes could not be read. Run `ckeel doctor --fix`."
    )


class StateError(ContextkeelError):
    """``.contextkeel/state.json`` is unreadable or from a newer schema."""

    default_user_message = (
        "This workspace was set up by a newer version of the tool. Run `ckeel upgrade`."
    )


__all__ = [
    "BackendUnavailable",
    "ContextkeelError",
    "RenderConflict",
    "StateError",
    "ToolchainError",
    "VaultError",
]
