"""Compatibility wrapper for enrichment schemas.

Canonical implementation lives in app.domains.enrich.schemas.enrichment.
"""

from app.domains.enrich.schemas.enrichment import EnrichRequest, EnrichResponse

__all__ = ["EnrichRequest", "EnrichResponse"]