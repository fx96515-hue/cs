"""Compatibility wrapper for peru_sourcing routes.

Canonical implementation lives in app.domains.peru_sourcing.api.routes.
"""

from app.domains.peru_sourcing.api.routes import *  # noqa: F401,F403
from app.domains.peru_sourcing.api.routes import router

__all__ = ["router"]
