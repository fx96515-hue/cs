"""Compatibility wrapper for transport-event routes.

Canonical implementation lives in app.domains.transport_events.api.routes.
"""

from app.domains.transport_events.api.routes import router

__all__ = ["router"]
