"""Compatibility wrapper for market routes.

Canonical implementation lives in app.domains.market.api.routes.
"""

from app.domains.market.api.routes import *  # noqa: F401,F403
from app.domains.market.api.routes import router

__all__ = ["router"]
