"""User-facing output, in two registers.

The product promise is that a developer never *has* to learn the name of an
internal tool — not that they are prevented from doing so. So the same
information is rendered two ways:

* **default** — internal tool names are rewritten to neutral equivalents
  ("code index", "notes viewer"). Someone who does not care about the
  internals is never made to care.
* **expert** — text passes through untouched: real names, real versions, real
  command lines. Enabled by ``--expert``, ``--verbose``, ``--json``, or
  ``CONTEXTKEEL_EXPERT=1``.

``INTERNAL_TERMS`` is a *mapping*, not a blocklist. Nothing is forbidden; the
neutral wording is only a default, and :mod:`contextkeel.expert` prints this
mapping so any neutral phrase can be translated back to the real thing.
"""

from __future__ import annotations

import contextlib
import json
import logging
import re
import sys
from dataclasses import dataclass, field

log = logging.getLogger("contextkeel")

#: Internal tool name -> what the default register calls it.
INTERNAL_TERMS: dict[str, str] = {
    "graphifyy": "code index",
    "graphify": "code index",
    "tree-sitter": "code index",
    "obsidian": "notes viewer",
}

_TERM_RE = re.compile(
    "|".join(sorted((re.escape(k) for k in INTERNAL_TERMS), key=len, reverse=True)),
    re.IGNORECASE,
)


@dataclass
class Output:
    """Global output configuration, owned by the CLI and read everywhere."""

    quiet: bool = False
    json_mode: bool = False
    expert: bool = False
    _records: list[dict] = field(default_factory=list)

    @property
    def register(self) -> str:
        # --json is always the expert register: a machine consumer parsing
        # "code index" instead of the real backend id is broken by design.
        return "expert" if (self.expert or self.json_mode) else "default"

    def render(self, text: str) -> str:
        """Apply the active register to a piece of text."""
        if self.register == "expert":
            return text
        return _TERM_RE.sub(lambda m: INTERNAL_TERMS[m.group(0).lower()], text)


#: Process-wide output state. Replaced wholesale by the CLI at startup.
out = Output()


def configure(
    *, quiet: bool = False, json_mode: bool = False, expert: bool = False
) -> Output:
    global out
    _use_utf8()
    out = Output(quiet=quiet, json_mode=json_mode, expert=expert)
    return out


def render(text: str) -> str:
    """Render ``text`` for the active register."""
    return out.render(text)


#: Windows consoles default to cp1252, which cannot encode these. Forcing
#: UTF-8 usually works, but a redirected or exotic stream may still refuse,
#: so keep an ASCII equivalent for every symbol we print. The same care
#: `platform.run` takes with subprocess output belongs on our own stdout.
_ASCII_FALLBACK = {"\u2192": "->", "\u2713": "OK", "\u2717": "X", "\u2026": "..."}


def _make_printable(text: str, stream) -> str:
    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
        return text
    except (UnicodeEncodeError, LookupError):
        for fancy, plain in _ASCII_FALLBACK.items():
            text = text.replace(fancy, plain)
        return text.encode(encoding, "replace").decode(encoding, "replace")


def _use_utf8() -> None:
    """Ask both streams for UTF-8; harmless where they already are."""
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError, OSError):
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]


def _emit(text: str, *, stream=None, force: bool = False) -> None:
    log.debug("emit: %s", text)  # log always records real names, to file only
    if out.json_mode:
        out._records.append({"message": text})
        return
    if out.quiet and not force:
        return
    target = stream or sys.stdout
    print(_make_printable(out.render(text), target), file=target)


def step(text: str) -> None:
    _emit(f"→ {text}")


def say(text: str) -> None:
    _emit(text)


def ok(text: str) -> None:
    _emit(f"✓ {text}")


def warn(text: str) -> None:
    _emit(f"! {text}", stream=sys.stderr, force=True)


def fail(text: str) -> None:
    _emit(f"✗ {text}", stream=sys.stderr, force=True)


def detail(text: str) -> None:
    """Expert-only line. Invisible in the default register."""
    log.debug("detail: %s", text)
    if out.register == "expert" and not out.json_mode:
        print(_make_printable(text, sys.stdout))


def emit_json(payload: dict) -> None:
    """Terminal output for ``--json``. Always the expert register."""
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


__all__ = [
    "INTERNAL_TERMS",
    "Output",
    "configure",
    "detail",
    "emit_json",
    "fail",
    "ok",
    "out",
    "render",
    "say",
    "step",
    "warn",
]
