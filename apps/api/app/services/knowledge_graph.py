"""Compatibility wrapper for knowledge_graph services.

Canonical implementation lives in app.domains.knowledge_graph.services.graph_service.
"""

import importlib

_canonical = importlib.import_module(
    "app.domains.knowledge_graph.services.graph_service"
)

__all__ = [name for name in dir(_canonical) if not name.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_canonical, _name)
