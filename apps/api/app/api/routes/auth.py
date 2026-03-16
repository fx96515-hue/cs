"""Compatibility wrapper for auth routes.

Canonical implementation lives in app.domains.auth.api.routes.
"""

from app.domains.auth.api.routes import *  # noqa: F401,F403
from app.domains.auth.api.routes import router

__all__ = ["router"]
