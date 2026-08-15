---
name: lang-python
description: Python idioms (defers to Vault/Context/Conventions.md)
globs: **/*.py
always_apply: false
---
# Python

Follow `Vault/Context/Conventions.md` first. Language idioms:

- Target modern Python (3.11+). Full type hints on public functions.
- Follow PEP 8; `snake_case` for functions/vars, `PascalCase` for classes.
- Prefer `pathlib` over `os.path`; f-strings over `%`/`.format`.
- Use dataclasses/pydantic for structured data; validate external input.
- Raise specific exceptions; never bare `except:`.
- Respect the project's tooling from `project.yml`: `uv`/`poetry`/`pip`,
  `ruff`/`black` for format/lint, `pytest` for tests (`test_*.py`).
- Keep side effects out of import time; guard scripts with `if __name__ == "__main__":`.
