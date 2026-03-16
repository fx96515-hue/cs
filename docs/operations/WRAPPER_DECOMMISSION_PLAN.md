# Wrapper Decommission Plan

## Goal
Retire legacy compatibility wrappers (`app.api.routes.*`, `app.schemas.*`, `app.services.*`) in controlled, non-breaking slices.

## Current State
- Canonical implementation is domain-first (`app.domains.*`).
- Compatibility wrappers still exist for migration safety and external import stability.
- Internal routing is now domain-based in `app/api/router.py`.

## Decommission Strategy
1. Freeze policy
- No new internal imports from wrapper paths.
- All new code must import canonical domain modules.

2. Usage audit on every slice
- Run:
  - `powershell -File scripts/maintenance/audit_wrapper_usage.ps1`
- Zero internal references required before removing a wrapper.

3. Removal waves
- Wave A: remove wrappers with zero internal references and no test dependencies.
- Wave B: move remaining tests to canonical imports.
- Wave C: remove remaining wrappers after one full release cycle.

4. Gate requirements per wave
- `ruff check app tests`
- `mypy --config-file ../../mypy.ini app`
- `pytest apps/api/tests -q`
- Frontend lint/build if web touched

## Immediate Actions Completed
- Internal API router switched to canonical domain imports.
- Test monkeypatch paths moved from wrappers to canonical modules for discovery/health/auto-outreach.
- Wrapper-usage audit script added.

## Risk Controls
- Small commit slices (`refactor`, `tests`, `docs`).
- Keep wrappers only where transitional compatibility is still needed.
- No silent breaking removal; each removal wave documented in baseline report.

