"""Single source of truth for the package version.

Read by hatchling at build time and by ``ckeel --version`` at runtime, so the
two can never disagree. Nothing else belongs in this module.
"""

__version__ = "0.1.0"
