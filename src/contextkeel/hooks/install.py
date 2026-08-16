"""Merging generated config into files a user may also own.

``.claude/settings.json`` and ``.cursor/hooks.json`` are shared: this tool owns
some entries, and the developer owns others. Replacing the file wholesale
would silently delete their permissions and their hooks, so generated entries
are tagged with ``_owner`` and merged in, leaving everything else untouched.
"""

from __future__ import annotations

import json
from typing import Any

OWNER = "contextkeel"

MERGEABLE = {".claude/settings.json", ".cursor/hooks.json"}


def is_mergeable(rel: str) -> bool:
    return rel.replace("\\", "/") in MERGEABLE


def merge(rel: str, generated: str, existing: str) -> str:
    """Merge ``generated`` into ``existing``, preserving user-owned entries."""
    try:
        new = json.loads(generated)
        old = json.loads(existing)
    except json.JSONDecodeError:
        # Unparseable existing file: do not try to be clever, keep ours and
        # let the caller's fingerprint check flag it.
        return generated

    rel = rel.replace("\\", "/")
    if rel == ".claude/settings.json":
        merged = _merge_claude(new, old)
    else:
        merged = _merge_cursor(new, old)
    return json.dumps(merged, indent=2) + "\n"


def _merge_claude(new: dict, old: dict) -> dict:
    merged: dict[str, Any] = dict(old)

    # Permissions: union of both allow-lists, ours plus anything they added.
    perms_new = new.get("permissions", {})
    perms_old = old.get("permissions", {})
    merged["permissions"] = {
        "allow": sorted(
            set(perms_old.get("allow", [])) | set(perms_new.get("allow", []))
        ),
        "deny": sorted(set(perms_old.get("deny", [])) | set(perms_new.get("deny", []))),
    }

    # Hooks: drop only the ones we previously wrote, then add ours back.
    hooks_old = old.get("hooks", {})
    hooks_new = new.get("hooks", {})
    merged_hooks: dict[str, list] = {}
    # Sorted: set iteration order varies per process (string hash
    # randomisation), which would reorder the JSON keys and make every
    # sync report a spurious config change.
    for event in sorted(set(hooks_old) | set(hooks_new)):
        kept = [entry for entry in hooks_old.get(event, []) if not _owned(entry)]
        merged_hooks[event] = kept + hooks_new.get(event, [])
    merged["hooks"] = merged_hooks
    return merged


def _merge_cursor(new: dict, old: dict) -> dict:
    merged: dict[str, Any] = dict(old)
    merged["version"] = new.get("version", old.get("version", 1))
    hooks_old = old.get("hooks", {})
    hooks_new = new.get("hooks", {})
    merged_hooks: dict[str, list] = {}
    # Sorted: set iteration order varies per process (string hash
    # randomisation), which would reorder the JSON keys and make every
    # sync report a spurious config change.
    for event in sorted(set(hooks_old) | set(hooks_new)):
        kept = [entry for entry in hooks_old.get(event, []) if not _owned(entry)]
        merged_hooks[event] = kept + hooks_new.get(event, [])
    merged["hooks"] = merged_hooks
    return merged


def _owned(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if entry.get("_owner") == OWNER:
        return True
    inner = entry.get("hooks")
    if isinstance(inner, list):
        return any(isinstance(h, dict) and h.get("_owner") == OWNER for h in inner)
    command = entry.get("command", "")
    return isinstance(command, str) and command.startswith(("ckeel ", "contextkeel "))


__all__ = ["MERGEABLE", "OWNER", "is_mergeable", "merge"]
