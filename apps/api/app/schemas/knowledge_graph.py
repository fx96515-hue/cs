"""Compatibility wrapper for knowledge_graph schemas.

Canonical implementation lives in app.domains.knowledge_graph.schemas.knowledge_graph.
"""

import importlib

_canonical = importlib.import_module("app.domains.knowledge_graph.schemas.knowledge_graph")

__all__ = [name for name in dir(_canonical) if not name.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_canonical, _name)
