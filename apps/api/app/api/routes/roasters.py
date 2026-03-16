"""Compatibility wrapper for roasters routes.

Canonical implementation lives in app.domains.roasters.api.routes.
"""

from app.domains.roasters.api.routes import *  # noqa: F401,F403
from app.domains.roasters.api.routes import router

__all__ = ["router"]
