"""Compatibility wrapper for ML prediction routes.

Canonical implementation lives in app.domains.ml_predictions.api.routes.
"""

from app.domains.ml_predictions.api.routes import router

__all__ = ["router"]
