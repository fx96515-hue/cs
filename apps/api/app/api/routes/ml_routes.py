"""Compatibility wrapper for ML training routes.

Canonical implementation lives in app.domains.ml_training.api.routes.
"""

from app.domains.ml_training.api.routes import router, train_freight_model

__all__ = ["router", "train_freight_model"]
