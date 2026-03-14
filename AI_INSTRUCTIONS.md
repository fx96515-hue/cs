# CoffeeStudio AI Instructions

Use this file as a short operational guide when changing CoffeeStudio.

## Read First

Before making changes, read:

1. `README.md`
2. `CODEBASE_MAP.md`
3. `ENTERPRISE_ROADBOOK.md`
4. `docs/operations/V0_SAFE_DELIVERY.md`

## Current Architecture

- Backend API routes live in `apps/api/app/api/routes/`
- SQLAlchemy models live in `apps/api/app/models/`
- provider clients live in `apps/api/app/providers/`
- business logic lives in `apps/api/app/services/`
- frontend app routes live in `apps/web/app/`
- shared browser API client lives in `apps/web/lib/api.ts`

Important: some older PR material refers to `apps/api/app/routes/`. That is not
the active route structure in the integrated branch.

## Non-Negotiable Rules

- Protect existing product logic first.
- Do not make destructive schema or auth changes without explicit need.
- Prefer additive adapters over broad rewrites.
- Do not claim a feature is production-ready unless it is actually verified.
- Do not introduce fake live data in dashboards that look operational.
- Keep secrets in local `.env`, never in tracked files.

## Backend Rules

- Keep routes thin.
- Put external integrations behind provider modules.
- Keep orchestration in services, not in route handlers.
- Use typed request/response models where the route already follows that pattern.
- Preserve current auth, rate limiting, and security middleware assumptions.

## Frontend Rules

- Reuse existing app structure and data flows.
- Use service-layer or `lib/api.ts` patterns already present in the repo.
- Prefer real backend wiring over static demo placeholders.
- Preserve keyboard access, loading states, error states, and empty states.

## PR721-Specific Guidance

The integrated PR721 scope is split into safe layers:

- frontend pages and adapters
- additive provider catalog modules
- additive monitoring and feature modules
- safe Alembic `0020` migration for new additive tables

Do not re-introduce:

- unsafe seed logic into existing core tables
- duplicate route trees
- inflated endpoint counts or coverage claims
- default credentials in docs

## Verification

Backend:

```bash
pytest apps/api/tests/test_auth.py \
  apps/api/tests/test_rate_limiting.py \
  apps/api/tests/test_pr721_dashboard_routes.py \
  apps/api/tests/test_semantic_search.py \
  apps/api/tests/test_scheduler_dashboard_routes.py \
  apps/api/tests/test_market_dashboard_routes.py \
  apps/api/tests/test_monitoring_dashboard_routes.py -q
```

Frontend:

```bash
cd apps/web
npm run build
```

## Good Default Workflow

1. Start from `origin/main` or the dedicated integration branch.
2. Integrate changes in small slices.
3. Run backend tests.
4. Run frontend build.
5. Only then prepare a merge recommendation.
