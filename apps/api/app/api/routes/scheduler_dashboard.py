"""Compatibility wrapper for scheduler dashboard routes.

Canonical implementation lives in app.domains.scheduler.api.routes.
"""

from app.domains.scheduler.api.routes import AsyncResult, celery, router

__all__ = ["router", "celery", "AsyncResult"]
