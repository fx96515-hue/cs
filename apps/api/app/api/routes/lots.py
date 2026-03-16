"""Compatibility wrapper for lots routes.

Canonical implementation lives in app.domains.lots.api.routes.
"""

from app.domains.lots.api.routes import *  # noqa: F401,F403
from app.domains.lots.api.routes import router

__all__ = ["router"]
