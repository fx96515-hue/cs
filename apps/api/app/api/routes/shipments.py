"""Compatibility wrapper for shipments routes.

Canonical implementation lives in app.domains.shipments.api.routes.
"""

from app.domains.shipments.api.routes import *  # noqa: F401,F403
from app.domains.shipments.api.routes import router

__all__ = ["router"]
