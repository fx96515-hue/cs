"""Compatibility wrapper for shipment schemas.

Canonical implementation lives in app.domains.shipments.schemas.shipment.
"""

import importlib

_canonical = importlib.import_module("app.domains.shipments.schemas.shipment")

__all__ = [name for name in dir(_canonical) if not name.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_canonical, _name)
