"""Compatibility wrapper for cooperatives routes.

Canonical implementation lives in app.domains.cooperatives.api.routes.
"""

from app.domains.cooperatives.api.routes import *  # noqa: F401,F403
from app.domains.cooperatives.api.routes import router

__all__ = ["router"]
