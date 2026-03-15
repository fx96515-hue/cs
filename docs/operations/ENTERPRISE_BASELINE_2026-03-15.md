# Enterprise Baseline Audit (2026-03-15)

## Scope

Repository: `CoffeeStudio`  
Branch: `audit/enterprise-baseline-20260315`

This baseline captures the current technical status before broader hardening/refactoring work.

## Verified Gates

- `docker compose config -q`: PASS
- `docker compose -f docker-compose.stack.yml config -q`: PASS
- `apps/api`: `pytest -q`: PASS (`651 passed, 3 skipped`)
- `apps/api`: `ruff check app tests`: PASS
- `apps/api`: `mypy --config-file ../../mypy.ini app`: PASS
- `apps/web`: `npm run lint`: PASS
- `apps/web`: `npx tsc --noEmit`: PASS
- `apps/web`: `npm run build`: PASS
- `docker compose up -d --build`: PASS
- `powershell -File scripts/win/smoke.ps1`: PASS

## Critical Findings (Phase 3 priority)

1. Broken integration smoke script (`scripts/integration_smoke_test.sh`)
- Status: FIXED
- Issue: merge-damaged structure (duplicate functions, malformed flow).
- Action: rebuilt script with deterministic phases, counters, auth flow, and clear failure handling.

2. Windows smoke auth false-negative
- Status: FIXED
- Issue: calls used non-canonical endpoints (`/cooperatives`, `/roasters`) and could lose bearer headers on redirect.
- Action: switched to canonical routes with trailing slash and fixed token-length output formatting.

## High-Priority Findings

1. Local security scan noise / temporary artifacts
- Status: PARTIAL
- Action: ignore rule added for local temp dumps (`.tmp_*.json`) to improve repo hygiene.

2. Frontend lint quality warning in report detail page
- Status: FIXED
- Action: removed synchronous `setState` call from `useEffect` path.

## Medium Findings

1. Formatting drift in backend codebase (`ruff format --check` reports many files)
- Status: OPEN
- Note: CI currently formats first and then checks; this does not block CI but indicates style drift.

2. Large working tree with concurrent in-flight hardening edits
- Status: OPEN
- Note: further changes should continue in small, scoped commits to avoid blast radius.

## Commits Created in This Audit Slice

- `5e136f6` `fix(smoke): restore integration script and clear frontend lint warning`
- `ce272a8` `fix(smoke-win): avoid auth header loss on redirected endpoints`

## Next Execution Slice

1. Normalize smoke/ops scripts (`scripts/smoke.sh`, `scripts/win/10_smoke_api.ps1`, `run_windows.ps1`) for consistent endpoint conventions and error handling.
2. Stabilize security scanning policy (focus on actionable HIGH/CRITICAL + handling unfixed OS CVEs consistently).
3. Start structured hardening pass on critical backend input boundaries and auth-adjacent endpoints.
