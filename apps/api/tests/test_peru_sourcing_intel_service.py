"""Tests for PeruRegionIntelService helpers."""

from app.services.peru_sourcing_intel import PeruRegionIntelService


def test_normalize_region_name_strips_trailing_parentheses():
    out = PeruRegionIntelService._normalize_region_name("Junín (Satipo/Chanchamayo)")
    assert out == "junin"


def test_normalize_region_name_collapses_whitespace():
    out = PeruRegionIntelService._normalize_region_name("  SAN   MARTÍN   ")
    assert out == "san martin"
