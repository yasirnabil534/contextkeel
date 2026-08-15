"""``project.yml`` model, auto-detection, and defaults.

Two hard rules, both from the product promise:

* **Never block on configuration.** A missing, empty or malformed
  ``project.yml`` is not an error — synthesise one from ``defaults`` and carry
  on. Blocking a developer on config is the one thing this tool must not do.
* **Never destroy comments.** ``project.yml`` is heavily commented and those
  comments are how a human understands it, so writes round-trip through
  ruamel.yaml rather than a plain dump.

``resolve()`` is pure: it returns a resolved copy and never writes. The caller
decides whether to persist.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

log = logging.getLogger("contextkeel")

AUTO = "auto"
ViewerPolicy = Literal["always", "auto", "never"]


def _is_auto(value: Any) -> bool:
    return value is None or value == "" or value == AUTO


class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore", validate_assignment=True)


class ProjectMeta(_Base):
    name: str = ""
    description: str = ""
    type: str = "fullstack"


class Frontend(_Base):
    platform: str = AUTO
    language: str = AUTO
    framework: str = AUTO
    package_manager: str = AUTO
    build_tool: str = AUTO
    styling: str = AUTO
    state: str = AUTO
    navigation: str = AUTO


class Backend(_Base):
    language: str = AUTO
    runtime: str = AUTO
    framework: str = AUTO
    package_manager: str = AUTO
    database: str = AUTO
    orm: str = AUTO


class Architecture(_Base):
    pattern: str = AUTO
    frontend_pattern: str = AUTO
    api_style: str = AUTO
    monorepo: str = AUTO
    notes: str = ""


class UI(_Base):
    mode: str = "agent"
    figma: str = ""


class Conventions(_Base):
    test_framework: str = AUTO
    e2e_framework: str = AUTO
    ci: str = AUTO
    commit_style: str = "conventional"
    formatter: str = AUTO
    linter: str = AUTO


class Context(_Base):
    """Where context lives, and the expert-facing overrides."""

    vault: str = "Vault"
    workspace: str = ".contextkeel"
    read_context_first: bool = True
    update_after_changes: bool = True
    #: Pin a specific index backend across machines. Empty = auto-select.
    backend: str = ""
    #: Notes-viewer install policy. Experts pin this; everyone else ignores it.
    viewer: ViewerPolicy = "auto"


class Config(_Base):
    project: ProjectMeta = Field(default_factory=ProjectMeta)
    frontend: Frontend = Field(default_factory=Frontend)
    backend: Backend = Field(default_factory=Backend)
    architecture: Architecture = Field(default_factory=Architecture)
    ui: UI = Field(default_factory=UI)
    conventions: Conventions = Field(default_factory=Conventions)
    context: Context = Field(default_factory=Context)
    defaults: dict[str, Any] = Field(default_factory=dict)

    @property
    def has_frontend(self) -> bool:
        return self.project.type in {"fullstack", "frontend", "mobile", "desktop"}

    @property
    def has_backend(self) -> bool:
        return self.project.type in {
            "fullstack",
            "backend",
            "api",
            "library",
            "cli",
        }


DEFAULTS: dict[str, Any] = {
    "type": "fullstack",
    "frontend": {
        "platform": "web",
        "language": "typescript",
        "framework": "react",
        "package_manager": "npm",
        "build_tool": "vite",
        "styling": "tailwind",
        "state": "none",
    },
    "backend": {
        "language": "typescript",
        "runtime": "node",
        "framework": "express",
        "package_manager": "npm",
        "database": "postgres",
        "orm": "prisma",
    },
    "test_framework": "vitest",
    "e2e_framework": "playwright",
    "formatter": "prettier",
    "linter": "eslint",
}


# --------------------------------------------------------------------------
# Load / save
# --------------------------------------------------------------------------


def config_path(root: Path) -> Path:
    return root / "project.yml"


def load(root: Path) -> Config:
    """Load ``project.yml``. Never raises — a broken file degrades to defaults."""
    path = config_path(root)
    if not path.is_file():
        log.debug("no project.yml at %s; using defaults", path)
        return Config(defaults=DEFAULTS)
    try:
        from ruamel.yaml import YAML

        yaml = YAML(typ="rt")
        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.load(fh) or {}
        plain = json.loads(json.dumps(raw, default=str))
        cfg = Config.model_validate(plain)
        if not cfg.defaults:
            cfg.defaults = DEFAULTS
        return cfg
    except Exception as exc:  # noqa: BLE001 - never block on config
        log.warning("project.yml unreadable (%s); using defaults", exc)
        return Config(defaults=DEFAULTS)


def save(cfg: Config, root: Path) -> None:
    """Write resolved values back, preserving the file's comments."""
    from ruamel.yaml import YAML

    path = config_path(root)
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True

    if path.is_file():
        with path.open("r", encoding="utf-8") as fh:
            doc = yaml.load(fh) or {}
    else:
        doc = {}

    payload = cfg.model_dump(exclude={"defaults"})
    for section, values in payload.items():
        if isinstance(values, dict):
            existing = doc.setdefault(section, {})
            for key, value in values.items():
                existing[key] = value
        else:
            doc[section] = values

    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        yaml.dump(doc, fh)
    tmp.replace(path)


# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _detect_frontend(root: Path, fe: Frontend) -> None:
    pkg = root / "package.json"
    if not pkg.is_file():
        return
    data = _read_json(pkg)
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

    if _is_auto(fe.framework):
        for dep, name in [
            ("next", "next"),
            ("nuxt", "nuxt"),
            ("@sveltejs/kit", "sveltekit"),
            ("@angular/core", "angular"),
            ("expo", "expo"),
            ("react-native", "react-native"),
            ("electron", "electron"),
            ("@tauri-apps/api", "tauri"),
            ("svelte", "svelte"),
            ("vue", "vue"),
            ("solid-js", "solid"),
            ("astro", "astro"),
            ("react", "react"),
        ]:
            if dep in deps:
                fe.framework = name
                break

    if _is_auto(fe.platform):
        if fe.framework in {"expo", "react-native", "ionic", "capacitor"}:
            fe.platform = "mobile"
        elif fe.framework in {"electron", "tauri"}:
            fe.platform = "desktop"
        elif fe.framework != AUTO:
            fe.platform = "web"

    if _is_auto(fe.language):
        fe.language = "typescript" if "typescript" in deps else "javascript"
    if _is_auto(fe.styling) and "tailwindcss" in deps:
        fe.styling = "tailwind"
    if _is_auto(fe.state):
        for dep, name in [
            ("@reduxjs/toolkit", "redux"),
            ("zustand", "zustand"),
            ("jotai", "jotai"),
            ("pinia", "pinia"),
        ]:
            if dep in deps:
                fe.state = name
                break
    if _is_auto(fe.package_manager):
        fe.package_manager = _detect_node_pm(root)
    if _is_auto(fe.build_tool):
        if fe.framework == "next":
            fe.build_tool = "next"
        elif (root / "vite.config.ts").exists() or (root / "vite.config.js").exists():
            fe.build_tool = "vite"


def _detect_node_pm(root: Path) -> str:
    for lock, name in [
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("bun.lockb", "bun"),
        ("package-lock.json", "npm"),
    ]:
        if (root / lock).is_file():
            return name
    return AUTO


def _detect_backend(root: Path, be: Backend) -> None:
    if (root / "pyproject.toml").is_file():
        text = (root / "pyproject.toml").read_text(encoding="utf-8", errors="replace")
        if _is_auto(be.language):
            be.language = "python"
        if _is_auto(be.runtime):
            be.runtime = "cpython"
        if _is_auto(be.framework):
            for needle, name in [
                ("fastapi", "fastapi"),
                ("django", "django"),
                ("flask", "flask"),
                ("litestar", "litestar"),
            ]:
                if needle in text.lower():
                    be.framework = name
                    break
        if _is_auto(be.package_manager):
            be.package_manager = "uv" if (root / "uv.lock").is_file() else "pip"
        if _is_auto(be.orm) and "sqlalchemy" in text.lower():
            be.orm = "sqlalchemy"
        return

    if (root / "go.mod").is_file():
        if _is_auto(be.language):
            be.language = "go"
        if _is_auto(be.runtime):
            be.runtime = "native"
        if _is_auto(be.package_manager):
            be.package_manager = "go"
        return

    if (root / "Cargo.toml").is_file():
        if _is_auto(be.language):
            be.language = "rust"
        if _is_auto(be.runtime):
            be.runtime = "native"
        if _is_auto(be.package_manager):
            be.package_manager = "cargo"
        return

    if any(root.glob("*.csproj")) or any(root.glob("*.sln")):
        if _is_auto(be.language):
            be.language = "csharp"
        if _is_auto(be.runtime):
            be.runtime = "dotnet"
        if _is_auto(be.package_manager):
            be.package_manager = "dotnet"
        return

    pkg = root / "package.json"
    if pkg.is_file():
        deps = {
            **_read_json(pkg).get("dependencies", {}),
            **_read_json(pkg).get("devDependencies", {}),
        }
        if _is_auto(be.language):
            be.language = "typescript" if "typescript" in deps else "javascript"
        if _is_auto(be.runtime):
            be.runtime = "node"
        if _is_auto(be.framework):
            for dep, name in [
                ("@nestjs/core", "nestjs"),
                ("fastify", "fastify"),
                ("hono", "hono"),
                ("express", "express"),
            ]:
                if dep in deps:
                    be.framework = name
                    break
        if _is_auto(be.orm):
            for dep, name in [
                ("prisma", "prisma"),
                ("drizzle-orm", "drizzle"),
                ("typeorm", "typeorm"),
            ]:
                if dep in deps:
                    be.orm = name
                    break
        if _is_auto(be.package_manager):
            be.package_manager = _detect_node_pm(root)


def _detect_conventions(root: Path, cfg: Config) -> None:
    c = cfg.conventions
    pkg = root / "package.json"
    deps: dict[str, Any] = {}
    if pkg.is_file():
        data = _read_json(pkg)
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

    if _is_auto(c.test_framework):
        if cfg.backend.language == "python":
            c.test_framework = "pytest"
        elif cfg.backend.language == "go":
            c.test_framework = "go-test"
        elif cfg.backend.language == "rust":
            c.test_framework = "cargo-test"
        elif cfg.backend.language == "csharp":
            c.test_framework = "xunit"
        elif "vitest" in deps:
            c.test_framework = "vitest"
        elif "jest" in deps:
            c.test_framework = "jest"

    if _is_auto(c.e2e_framework):
        if "@playwright/test" in deps or "playwright" in deps:
            c.e2e_framework = "playwright"
        elif "cypress" in deps:
            c.e2e_framework = "cypress"

    if _is_auto(c.ci):
        if (root / ".github" / "workflows").is_dir():
            c.ci = "github-actions"
        elif (root / ".gitlab-ci.yml").is_file():
            c.ci = "gitlab-ci"

    if _is_auto(c.linter):
        if cfg.backend.language == "python":
            c.linter = "ruff"
        elif "eslint" in deps:
            c.linter = "eslint"

    if _is_auto(c.formatter):
        if cfg.backend.language == "python":
            c.formatter = "ruff"
        elif "prettier" in deps:
            c.formatter = "prettier"


def _detect_architecture(root: Path, arch: Architecture) -> None:
    if _is_auto(arch.monorepo):
        markers = ["pnpm-workspace.yaml", "turbo.json", "nx.json", "lerna.json"]
        arch.monorepo = "yes" if any((root / m).is_file() for m in markers) else "no"
    if _is_auto(arch.api_style):
        arch.api_style = "rest"


BACKEND_MANIFESTS = ("pyproject.toml", "go.mod", "Cargo.toml", "pom.xml", "build.gradle")


def _infer_type(root: Path) -> str:
    """Work out which tiers a repository actually has.

    The "works with nothing configured" rule must not invent tiers that plainly
    do not exist: a Python CLI with no ``package.json`` should never be told it
    has a React frontend. Only a repository with no recognisable manifest at
    all falls through to the full-stack default.
    """
    has_frontend = False
    pkg = root / "package.json"
    if pkg.is_file():
        data = _read_json(pkg)
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        has_frontend = any(
            marker in deps
            for marker in (
                "react", "next", "vue", "nuxt", "svelte", "@sveltejs/kit",
                "@angular/core", "solid-js", "astro", "react-native", "expo",
                "electron", "@tauri-apps/api", "ionic", "capacitor",
            )
        )

    has_backend = any((root / m).is_file() for m in BACKEND_MANIFESTS) or any(
        root.glob("*.csproj")
    )
    if pkg.is_file() and not has_frontend:
        has_backend = True  # a Node service

    if has_frontend and has_backend:
        return "fullstack"
    if has_frontend:
        return "frontend"
    if has_backend:
        return "backend"
    return ""


def _apply_defaults(cfg: Config, detected_backend: bool, detected_frontend: bool) -> None:
    d = cfg.defaults or DEFAULTS
    fe_d = d.get("frontend", {})
    be_d = d.get("backend", {})

    if _is_auto(cfg.project.type):
        cfg.project.type = d.get("type", "fullstack")

    # Defaults describe a TypeScript/React/Express stack. Applying them on top
    # of a *detected* stack produces nonsense ("express/python"), so they only
    # fill in a tier that detection found nothing for at all.
    if cfg.has_frontend and not detected_frontend:
        for key, value in fe_d.items():
            if hasattr(cfg.frontend, key) and _is_auto(getattr(cfg.frontend, key)):
                setattr(cfg.frontend, key, value)
    if cfg.has_backend and not detected_backend:
        for key, value in be_d.items():
            if hasattr(cfg.backend, key) and _is_auto(getattr(cfg.backend, key)):
                setattr(cfg.backend, key, value)

    for key in ("test_framework", "e2e_framework", "formatter", "linter"):
        if _is_auto(getattr(cfg.conventions, key)) and key in d:
            setattr(cfg.conventions, key, d[key])

    # Anything still unresolved is genuinely unknown, not a blocker.
    for section in (cfg.frontend, cfg.backend, cfg.architecture, cfg.conventions):
        for key, value in section.model_dump().items():
            if _is_auto(value) and isinstance(value, str):
                setattr(section, key, "none" if key in {"state", "orm"} else "unknown")


def resolve(cfg: Config, root: Path) -> Config:
    """Return a copy with every ``auto``/empty field filled in.

    Detection first, then the ``defaults`` block, then a neutral placeholder.
    Pure: never writes.
    """
    resolved = cfg.model_copy(deep=True)

    if _is_auto(resolved.project.name):
        resolved.project.name = root.name

    # Infer which tiers exist before resolving them, so a single-tier project
    # is not handed a phantom second tier from the defaults block.
    if _is_auto(cfg.project.type) or cfg.project.type == "fullstack":
        inferred = _infer_type(root)
        if inferred:
            resolved.project.type = inferred

    if resolved.has_frontend:
        _detect_frontend(root, resolved.frontend)
    if resolved.has_backend:
        _detect_backend(root, resolved.backend)
    _detect_architecture(root, resolved.architecture)
    _detect_conventions(root, resolved)
    _apply_defaults(
        resolved,
        detected_backend=not _is_auto(resolved.backend.language),
        detected_frontend=not _is_auto(resolved.frontend.framework),
    )
    return resolved


def summary(cfg: Config) -> str:
    """One-line human summary of the resolved stack."""
    parts: list[str] = [cfg.project.type]
    if cfg.has_frontend and cfg.frontend.framework not in {"unknown", "none"}:
        parts.append(f"{cfg.frontend.framework}/{cfg.frontend.language}")
    if cfg.has_backend and cfg.backend.framework not in {"unknown", "none"}:
        parts.append(f"{cfg.backend.framework}/{cfg.backend.language}")
    elif cfg.has_backend and cfg.backend.language not in {"unknown", "none"}:
        parts.append(cfg.backend.language)
    return " · ".join(parts)


__all__ = [
    "AUTO",
    "DEFAULTS",
    "Config",
    "config_path",
    "load",
    "resolve",
    "save",
    "summary",
]
