"""Compatibility wrapper for peru_sourcing schemas.

Canonical implementation lives in app.domains.peru_sourcing.schemas.peru_sourcing.
"""

import importlib

_canonical = importlib.import_module("app.domains.peru_sourcing.schemas.peru_sourcing")

__all__ = [name for name in dir(_canonical) if not name.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_canonical, _name)
