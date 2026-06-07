"""Compatibility wrapper for Peru region seed service.

Canonical implementation lives in app.domains.regions.services.peru_seed.
"""

from app.domains.regions.services.peru_seed import DEFAULT_REGIONS, seed_default_regions

__all__ = ["DEFAULT_REGIONS", "seed_default_regions"]
