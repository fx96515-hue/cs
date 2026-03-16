"""Compatibility wrapper for transport-event schemas.

Canonical implementation lives in app.domains.transport_events.schemas.transport_event.
"""

from app.domains.transport_events.schemas.transport_event import (
    TransportEventCreate,
    TransportEventOut,
)

__all__ = ["TransportEventCreate", "TransportEventOut"]