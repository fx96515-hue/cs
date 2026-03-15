# Enterprise Baseline Audit (2026-03-15)

## Scope

Repository: `CoffeeStudio`  
Branch: `audit/enterprise-baseline-20260315`

This baseline captures the current technical status before broader hardening/refactoring work.

## Verified Gates

- `docker compose config -q`: PASS
- `docker compose -f docker-compose.stack.yml config -q`: PASS
- `apps/api`: `pytest -q`: PASS (`660 passed, 3 skipped`)
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

3. Frontend Docker image critical CVE (zlib)
- Status: FIXED
- Issue: `coffeestudio-frontend:local` reported `CVE-2026-22184` (CRITICAL, fixed version available).
- Action: upgraded `zlib` in frontend Docker base stage (`apk upgrade --no-cache zlib`) and re-scanned.
- Validation: Trivy HIGH/CRITICAL result is now clean for frontend image.

4. Insecure local defaults and broad local port exposure in compose/scripts
- Status: FIXED
- Issue: permissive defaults (`adminadmin`, weak JWT fallback) and non-loopback published ports increased local attack surface.
- Action: hardened compose and Windows scripts:
  - bind published dev ports to loopback (`127.0.0.1`)
  - require `JWT_SECRET` in compose runtime
  - require explicit admin passwords for Grafana/Keycloak stack services
  - generate strong local secrets automatically in `run_windows.ps1`
  - removed implicit `adminadmin` fallback in setup scripts

5. Auth email matching could fail on mixed-case input
- Status: FIXED
- Issue: login/bootstrap user lookup compared emails case-sensitively.
- Action: normalized email lookup to case-insensitive query paths and added regression coverage.

6. Dev bootstrap endpoint reachable from non-local clients in dev/test
- Status: FIXED
- Issue: `/auth/dev/bootstrap` had no client-origin boundary beyond environment gating.
- Action: enforced loopback-only access and added tests for local/remote host detection.

7. Circuit reset endpoint accepted unbounded provider keys and returned 200 on unknown provider
- Status: FIXED
- Issue: `/data-health/reset-circuit/{provider}` accepted broad input and mixed errors into success responses.
- Action: enforced bounded provider key validation and returned proper `404` for unknown providers.

8. Pipeline trigger endpoint accepted broad source-name input
- Status: FIXED
- Issue: `/pipeline/trigger/{source_name}` accepted broad arbitrary path values.
- Action: added bounded/pattern-validated path input and canonical alias mapping for supported trigger sources.

## High-Priority Findings

1. Local security scan noise / temporary artifacts
- Status: IMPROVED
- Action: ignore rule added for local temp dumps (`.tmp_*.json`) to improve repo hygiene.

2. Frontend lint quality warning in report detail page
- Status: FIXED
- Action: removed synchronous `setState` call from `useEffect` path.

3. Frontend detail/dashboard layout inconsistencies across pages
- Status: PARTIAL
- Action: standardized shared `content` container usage and unified detail page wrappers/alerts on high-traffic pages.
- Remaining exception: `apps/web/app/analyst/page.tsx` keeps dedicated `chatLayout` by design.

## Medium Findings

1. Formatting drift in backend codebase (`ruff format --check` reports many files)
- Status: OPEN
- Note: CI currently formats first and then checks; this does not block CI but indicates style drift.

2. KI chat page had non-standard root wrapper
- Status: FIXED
- Action: aligned to shared `content` wrapper while preserving full-height chat behavior.

## Commits Created in This Audit Slice

- `5e136f6` `fix(smoke): restore integration script and clear frontend lint warning`
- `ce272a8` `fix(smoke-win): avoid auth header loss on redirected endpoints`
- `1fe0eae` `docs(audit): add enterprise baseline status and priorities`
- `43c6e60` `fix(smoke-win): silence expected health probe curl noise`
- `f6051db` `harden(docker): patch frontend image zlib critical CVE`
- `13de8f4` `harden(local): enforce secure compose defaults and bootstrap secrets`
- `fd40d1e` `improve(frontend): align lot detail page with shared dashboard patterns`
- `557c055` `improve(frontend): unify detail-page wrapper and success alert classes`
- `c0606fa` `improve(frontend): standardize page content wrapper on key dashboards`
- `acf2309` `improve(frontend): align content container usage across operations pages`
- `b717d88` `improve(frontend): apply shared content layout to additional workflow pages`
- `3ea950a` `chore(repo): remove stale pre-commit backup config`
- `d8cbe8e` `improve(frontend): align KI page wrapper with shared content layout`
- `22f5a18` `docs(audit): update baseline with current hardening progress`
- `2b5ea9d` `harden(auth): normalize email matching for login and bootstrap`
- `cc88614` `chore(repo): remove stale QA backup file`
- `c2b7db7` `docs(audit): record auth hardening and latest validation`
- `25ab7d4` `chore(repo): deduplicate and normalize gitignore rules`
- `55d3469` `harden(auth): restrict dev bootstrap endpoint to loopback clients`
- `15cc237` `harden(api): enforce provider validation on circuit reset endpoint`
- `4739d32` `docs(audit): record circuit-reset validation hardening`
- `b162e47` `harden(api): validate pipeline trigger source names and aliases`

## Next Execution Slice

1. Run targeted backend hardening pass for input validation and defensive boundaries on auth-adjacent and mutation endpoints.
2. Close remaining frontend consistency gap for special chat layouts via shared utility classes (without redesign).
3. Continue repo hygiene and documentation hardening (`.dockerignore`/dev docs/checklist synchronization).
