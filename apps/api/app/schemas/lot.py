"""Compatibility wrapper for lot schemas.

Canonical implementation lives in app.domains.lots.schemas.lot.
"""

import importlib

_canonical = importlib.import_module("app.domains.lots.schemas.lot")

__all__ = [name for name in dir(_canonical) if not name.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_canonical, _name)
