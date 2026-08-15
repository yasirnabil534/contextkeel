"""Bundled, offline code indexer.

Ships inside the package and needs no network and no external binary, which is
the whole point: when the preferred backend is unavailable the product must
degrade, not break.

Two levels of degradation live here. Normally this parses real syntax trees
via tree-sitter. If even that import fails, it falls back again to a regex
scan rather than raising — there must always be *some* index.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from contextkeel.graph.base import (
    Community,
    Edge,
    EdgeKind,
    IndexResult,
    Node,
    NodeKind,
)

log = logging.getLogger("contextkeel")

MAX_FILES = 20_000
MAX_FILE_BYTES = 1_500_000

ALWAYS_SKIP = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "target",
    ".next",
    ".nuxt",
    ".turbo",
    ".cache",
    ".contextkeel",
    ".idea",
    ".vscode",
    "vendor",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "coverage",
    ".gradle",
    "bin",
    "obj",
}


@dataclass(frozen=True)
class LanguageSpec:
    language: str
    defs: dict[str, NodeKind]
    imports: tuple[str, ...]


# Node types are tree-sitter grammar names, not ours.
SPECS: dict[str, LanguageSpec] = {
    ".py": LanguageSpec(
        "python",
        {
            "function_definition": NodeKind.FUNCTION,
            "class_definition": NodeKind.CLASS,
        },
        ("import_statement", "import_from_statement"),
    ),
    ".ts": LanguageSpec(
        "typescript",
        {
            "function_declaration": NodeKind.FUNCTION,
            "class_declaration": NodeKind.CLASS,
            "method_definition": NodeKind.METHOD,
            "interface_declaration": NodeKind.CLASS,
        },
        ("import_statement",),
    ),
    ".tsx": LanguageSpec(
        "tsx",
        {
            "function_declaration": NodeKind.FUNCTION,
            "class_declaration": NodeKind.CLASS,
            "method_definition": NodeKind.METHOD,
        },
        ("import_statement",),
    ),
    ".js": LanguageSpec(
        "javascript",
        {
            "function_declaration": NodeKind.FUNCTION,
            "class_declaration": NodeKind.CLASS,
            "method_definition": NodeKind.METHOD,
        },
        ("import_statement",),
    ),
    ".jsx": LanguageSpec(
        "javascript",
        {
            "function_declaration": NodeKind.FUNCTION,
            "class_declaration": NodeKind.CLASS,
            "method_definition": NodeKind.METHOD,
        },
        ("import_statement",),
    ),
    ".go": LanguageSpec(
        "go",
        {
            "function_declaration": NodeKind.FUNCTION,
            "method_declaration": NodeKind.METHOD,
            "type_declaration": NodeKind.CLASS,
        },
        ("import_declaration",),
    ),
    ".rs": LanguageSpec(
        "rust",
        {
            "function_item": NodeKind.FUNCTION,
            "struct_item": NodeKind.CLASS,
            "enum_item": NodeKind.CLASS,
            "trait_item": NodeKind.CLASS,
        },
        ("use_declaration",),
    ),
    ".java": LanguageSpec(
        "java",
        {
            "class_declaration": NodeKind.CLASS,
            "method_declaration": NodeKind.METHOD,
            "interface_declaration": NodeKind.CLASS,
        },
        ("import_declaration",),
    ),
    ".cs": LanguageSpec(
        "csharp",
        {
            "class_declaration": NodeKind.CLASS,
            "method_declaration": NodeKind.METHOD,
            "interface_declaration": NodeKind.CLASS,
        },
        ("using_directive",),
    ),
    ".rb": LanguageSpec(
        "ruby",
        {
            "method": NodeKind.METHOD,
            "class": NodeKind.CLASS,
            "module": NodeKind.MODULE,
        },
        ("call",),
    ),
}

_REGEX_DEFS = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?"
    r"(?:def|class|func|fn|function|struct|trait|interface|type)\s+([A-Za-z_]\w*)",
    re.M,
)
_REGEX_IMPORTS = re.compile(
    r"""^\s*(?:import\s+(?:[\w{}\s,*]+\s+from\s+)?['"]?([\w./@\-]+)|"""
    r"""from\s+([\w.]+)\s+import|use\s+([\w:]+)|require\(['"]([\w./@\-]+))""",
    re.M,
)


class GitIgnore:
    """Small ``.gitignore`` matcher.

    Deliberately does not shell out to git: git may be absent, and this needs
    to work in a plain directory that was never a repository.
    """

    def __init__(self, patterns: list[str]) -> None:
        self.negations: list[str] = []
        self.patterns: list[str] = []
        for raw in patterns:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("!"):
                self.negations.append(line[1:].strip("/"))
            else:
                self.patterns.append(line.strip("/"))

    @classmethod
    def load(cls, root: Path) -> GitIgnore:
        path = root / ".gitignore"
        if not path.is_file():
            return cls([])
        try:
            return cls(path.read_text(encoding="utf-8", errors="replace").splitlines())
        except OSError:
            return cls([])

    def _matches(self, rel: str, patterns: list[str]) -> bool:
        from fnmatch import fnmatch

        parts = rel.split("/")
        for pattern in patterns:
            if fnmatch(rel, pattern) or fnmatch(rel, f"{pattern}/*"):
                return True
            if any(fnmatch(part, pattern) for part in parts):
                return True
        return False

    def ignored(self, rel: str) -> bool:
        if self._matches(rel, self.negations):
            return False
        return self._matches(rel, self.patterns)


class FallbackBackend:
    """Always-available indexer bundled with the package."""

    name = "builtin"
    priority = 10

    def is_available(self) -> bool:
        # True even without tree-sitter: the regex path still produces an index.
        return True

    # -- public API ---------------------------------------------------------

    def build(self, root: Path) -> IndexResult:
        return self._index(root)

    def update(self, root: Path) -> IndexResult:
        # A full pass is already fast for this backend; incremental state would
        # cost more complexity than it saves.
        return self._index(root)

    def query(self, root: Path, q: str) -> list[Node]:
        result = self._index(root)
        needle = q.lower()
        return [
            n
            for n in result.nodes
            if needle in n.name.lower() or needle in n.path.lower()
        ]

    # -- internals ----------------------------------------------------------

    def _index(self, root: Path) -> IndexResult:
        ignore = GitIgnore.load(root)
        files = self._collect(root, ignore)

        nodes: list[Node] = []
        edges: list[Edge] = []
        truncated = len(files) >= MAX_FILES
        parsed_with = "regex"

        module_ids: dict[str, str] = {}
        for path in files:
            rel = path.relative_to(root).as_posix()
            module_id = rel
            module_ids[self._module_key(rel)] = module_id
            nodes.append(
                Node(id=module_id, kind=NodeKind.MODULE, path=rel, name=path.stem)
            )

        for path in files:
            rel = path.relative_to(root).as_posix()
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
                source = path.read_bytes()
            except OSError:
                continue

            spec = SPECS.get(path.suffix.lower())
            defs: list[tuple[str, NodeKind, int]] = []
            imports: list[str] = []

            if spec is not None:
                extracted = self._parse_tree_sitter(source, spec)
                if extracted is not None:
                    defs, imports = extracted
                    parsed_with = "tree-sitter"
            if not defs and not imports:
                defs, imports = self._parse_regex(source)

            for name, kind, line in defs:
                nodes.append(
                    Node(
                        id=f"{rel}::{name}",
                        kind=kind,
                        path=rel,
                        name=name,
                        line=line,
                    )
                )
                edges.append(
                    Edge(src=rel, dst=f"{rel}::{name}", kind=EdgeKind.CONTAINS)
                )

            for target in imports:
                resolved = self._resolve_import(target, rel, module_ids)
                if resolved and resolved != rel:
                    edges.append(Edge(src=rel, dst=resolved, kind=EdgeKind.IMPORTS))

        communities = self._communities(nodes)
        return IndexResult(
            nodes=nodes,
            edges=edges,
            communities=communities,
            backend_name=self.name,
            generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
            stats={
                "files": len(files),
                "parser": parsed_with,
                "truncated": truncated,
                "max_files": MAX_FILES,
            },
        )

    def _collect(self, root: Path, ignore: GitIgnore) -> list[Path]:
        found: list[Path] = []
        for path in sorted(root.rglob("*")):
            if len(found) >= MAX_FILES:
                break
            if path.is_dir():
                continue
            if any(part in ALWAYS_SKIP for part in path.parts):
                continue
            if path.suffix.lower() not in SPECS:
                continue
            rel = path.relative_to(root).as_posix()
            if ignore.ignored(rel):
                continue
            found.append(path)
        return found

    def _parse_tree_sitter(
        self, source: bytes, spec: LanguageSpec
    ) -> tuple[list[tuple[str, NodeKind, int]], list[str]] | None:
        try:
            from tree_sitter_language_pack import get_parser

            parser = get_parser(spec.language)
            tree = parser.parse(source)
        except Exception as exc:  # noqa: BLE001 - degrade to regex, never raise
            log.debug("tree-sitter unavailable for %s (%s)", spec.language, exc)
            return None

        defs: list[tuple[str, NodeKind, int]] = []
        imports: list[str] = []
        stack = [tree.root_node]
        while stack:
            node = stack.pop()
            kind = spec.defs.get(node.type)
            if kind is not None:
                name_node = node.child_by_field_name("name")
                if name_node is not None:
                    defs.append(
                        (
                            source[name_node.start_byte : name_node.end_byte].decode(
                                "utf-8", "replace"
                            ),
                            kind,
                            node.start_point[0] + 1,
                        )
                    )
            elif node.type in spec.imports:
                text = source[node.start_byte : node.end_byte].decode(
                    "utf-8", "replace"
                )
                imports.extend(self._import_targets(text))
            stack.extend(node.children)
        return defs, imports

    def _parse_regex(
        self, source: bytes
    ) -> tuple[list[tuple[str, NodeKind, int]], list[str]]:
        text = source.decode("utf-8", "replace")
        defs = [
            (m.group(1), NodeKind.UNKNOWN, text[: m.start()].count("\n") + 1)
            for m in _REGEX_DEFS.finditer(text)
        ]
        imports = [
            next(g for g in m.groups() if g) for m in _REGEX_IMPORTS.finditer(text)
        ]
        return defs, imports

    @staticmethod
    def _import_targets(text: str) -> list[str]:
        found = re.findall(r"""['"]([^'"]+)['"]""", text)
        if found:
            return found
        words = re.findall(r"[\w./:]+", text)
        return words[1:2] if len(words) > 1 else []

    @staticmethod
    def _module_key(rel: str) -> str:
        return rel.rsplit(".", 1)[0].replace("/", ".")

    def _resolve_import(
        self, target: str, from_rel: str, module_ids: dict[str, str]
    ) -> str | None:
        cleaned = target.strip().strip("./").replace("/", ".").replace(":", ".")
        if not cleaned:
            return None
        if cleaned in module_ids:
            return module_ids[cleaned]
        # Relative import: resolve against the importing file's package.
        base = from_rel.rsplit("/", 1)[0].replace("/", ".") if "/" in from_rel else ""
        if base:
            candidate = f"{base}.{cleaned}"
            if candidate in module_ids:
                return module_ids[candidate]
        for key, value in module_ids.items():
            if key.endswith(f".{cleaned}") or key == cleaned:
                return value
        return None

    @staticmethod
    def _communities(nodes: list[Node]) -> list[Community]:
        """Group by directory — good enough for navigation, which is the job."""
        buckets: dict[str, list[str]] = {}
        for node in nodes:
            if node.kind is not NodeKind.MODULE:
                continue
            directory = node.path.rsplit("/", 1)[0] if "/" in node.path else "."
            buckets.setdefault(directory, []).append(node.id)
        return [
            Community(id=directory, label=directory, members=tuple(sorted(members)))
            for directory, members in sorted(buckets.items())
        ]


__all__ = ["MAX_FILES", "FallbackBackend", "GitIgnore"]
