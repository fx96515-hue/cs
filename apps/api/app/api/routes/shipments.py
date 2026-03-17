"""Compatibility wrapper for shipments routes.

Canonical implementation lives in app.domains.shipments.api.routes.
"""

import importlib

_canonical = importlib.import_module("app.domains.shipments.api.routes")

__all__ = [name for name in dir(_canonical) if not name.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_canonical, _name)
