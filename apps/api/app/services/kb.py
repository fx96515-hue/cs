"""Compatibility wrapper for knowledge-base service.

Canonical implementation lives in app.domains.kb.services.seed.
"""

from app.domains.kb.services.seed import DEFAULT_DOCS, seed_default_kb

__all__ = ["DEFAULT_DOCS", "seed_default_kb"]