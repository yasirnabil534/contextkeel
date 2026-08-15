# Releasing

1. Update `CHANGELOG.md` under a new version heading.
2. Bump `__version__` in `src/contextkeel/__about__.py` — the single source of
   truth for both hatchling and `ckeel --version`.
3. Commit, then tag: `git tag v0.1.0 && git push --tags`.
4. CI verifies the tag matches the package version, builds, and publishes via
   PyPI Trusted Publishing (OIDC — no API token is stored in this repo).
5. A smoke job then installs the published version in a bare container and
   checks `ckeel --version`.

To rehearse without publishing for real, run the Release workflow manually with
`test_pypi` enabled.
