"""Compatibility wrapper for report generation service.

Canonical implementation lives in app.domains.reports.services.report_builder.
"""

from app.domains.reports.services.report_builder import (
    _fmt_obs,
    _latest_by_key,
    generate_daily_report,
)

__all__ = ["generate_daily_report", "_latest_by_key", "_fmt_obs"]
