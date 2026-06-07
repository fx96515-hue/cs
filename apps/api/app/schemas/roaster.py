"""Compatibility wrapper for roaster schemas.

Canonical implementation lives in app.domains.roasters.schemas.roaster.
"""

import importlib

_canonical = importlib.import_module("app.domains.roasters.schemas.roaster")

__all__ = [name for name in dir(_canonical) if not name.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_canonical, _name)
