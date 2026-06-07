"""Compatibility wrapper for auth schemas.

Canonical implementation lives in app.domains.auth.schemas.auth.
"""

import importlib

_canonical = importlib.import_module("app.domains.auth.schemas.auth")

__all__ = [name for name in dir(_canonical) if not name.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_canonical, _name)
