"""Unit tests for the country_config module."""

from __future__ import annotations

import pytest
import sys

from app.services.country_config import (
    COUNTRY_CONFIGS,
    SUPPORTED_COUNTRIES,
    CountryConfig,
    HarvestCalendar,
    get_active_countries,
    get_country_config,
)


# ---------------------------------------------------------------------------
# get_country_config
# ---------------------------------------------------------------------------


def test_get_country_config_valid_codes():
    for code in ["PE", "CO", "ET", "BR"]:
        cfg = get_country_config(code)
        assert cfg is not None
        assert isinstance(cfg, CountryConfig)
        assert cfg.code == code


def test_get_country_config_case_insensitive():
    assert get_country_config("pe") == get_country_config("PE")
    assert get_country_config("co") == get_country_config("CO")


def test_get_country_config_unknown_returns_none(caplog):
    import logging

    with caplog.at_level(logging.WARNING, logger="app.services.country_config"):
        result = get_country_config("XX")
    assert result is None
    assert "XX" in caplog.text


# ---------------------------------------------------------------------------
# CountryConfig fields
# ---------------------------------------------------------------------------


def test_all_countries_have_required_fields():
    for code, cfg in COUNTRY_CONFIGS.items():
        assert cfg.currency, f"{code}: missing currency"
        assert cfg.currency_symbol, f"{code}: missing currency_symbol"
        assert cfg.flag_emoji, f"{code}: missing flag_emoji"
        assert cfg.data_source.name, f"{code}: missing data_source.name"
        assert cfg.data_source.url, f"{code}: missing data_source.url"
        assert cfg.ml_country_feature == code, f"{code}: ml_country_feature mismatch"
        assert cfg.default_port, f"{code}: missing default_port"


def test_colombia_currency_symbol_not_ambiguous():
    """Colombia's symbol must not be bare '$' to avoid confusion with USD."""
    cfg = get_country_config("CO")
    assert cfg is not None
    assert cfg.currency_symbol != "$", "Use 'COP$' to avoid confusion with USD"


def test_discovery_queries_non_empty():
    for code, cfg in COUNTRY_CONFIGS.items():
        assert len(cfg.discovery_cooperative_queries) > 0, f"{code}: no coop queries"
        assert len(cfg.discovery_roaster_queries) > 0, f"{code}: no roaster queries"


# ---------------------------------------------------------------------------
# HarvestCalendar year-wrap logic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "start, end, expected_wraps",
    [
        (4, 9, False),  # Peru: Apr–Sep, no wrap
        (5, 9, False),  # Brazil: May–Sep, no wrap
        (10, 2, True),  # Colombia: Oct–Feb, wraps year
        (10, 1, True),  # Ethiopia: Oct–Jan, wraps year
    ],
)
def test_harvest_calendar_wraps_year(start, end, expected_wraps):
    cal = HarvestCalendar(main_crop_start=start, main_crop_end=end)
    assert cal.wraps_year is expected_wraps


# ---------------------------------------------------------------------------
# get_active_countries with feature flag
# ---------------------------------------------------------------------------


def test_get_active_countries_default_returns_only_peru(monkeypatch):
    country_config_module = sys.modules[get_active_countries.__module__]
    monkeypatch.setattr(country_config_module, "MULTI_COUNTRY_ENABLED", False)

    active = get_active_countries()
    assert len(active) == 1
    assert active[0].code == "PE"

    country_config_module = sys.modules[get_active_countries.__module__]
    monkeypatch.setattr(country_config_module, "MULTI_COUNTRY_ENABLED", True)

    active = get_active_countries()
    codes = {cfg.code for cfg in active}
    assert codes == set(SUPPORTED_COUNTRIES)


# ---------------------------------------------------------------------------
# SUPPORTED_COUNTRIES list
# ---------------------------------------------------------------------------


def test_supported_countries_matches_config_keys():
    assert set(SUPPORTED_COUNTRIES) == set(COUNTRY_CONFIGS.keys())
