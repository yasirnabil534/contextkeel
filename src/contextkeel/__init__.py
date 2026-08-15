"""contextkeel — a self-maintaining agent context workspace for any repo.

Kept free of side effects on purpose: no config loading, no filesystem access,
no subprocess calls at import time. ``ckeel --help`` must stay fast, so heavy
submodules are imported lazily by the CLI rather than re-exported here.
"""

from contextkeel.__about__ import __version__

__all__ = ["__version__"]
