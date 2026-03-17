"""Compatibility wrapper for market schemas.

Canonical implementation lives in app.domains.market.schemas.market.
"""

import importlib

_canonical = importlib.import_module("app.domains.market.schemas.market")

__all__ = [name for name in dir(_canonical) if not name.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_canonical, _name)
