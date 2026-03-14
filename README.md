# CoffeeStudio Platform

CoffeeStudio is a data and operations platform for specialty coffee workflows, with
Peru sourcing intelligence, market monitoring, entity management, reporting, and
AI-assisted analysis.

This branch includes the enterprise integration work for PR721. The new UI areas
for `pipeline`, `features`, `search`, `ki`, `markt`, and `scheduler` are wired to
real backend adapters instead of demo-only placeholders. Additional provider and
monitoring modules from PR721 were integrated as safe, additive capabilities.

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 16, TypeScript, React Query |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic |
| Database | PostgreSQL |
| Cache / Queue | Redis, Celery, Celery Beat |
| Auth | JWT bearer auth, cookie migration path prepared |
| Runtime | Docker Compose |

## Current Product Areas

Main routes currently available in the integrated frontend:

- `/dashboard`
- `/cooperatives`
- `/roasters`
- `/lots`
- `/shipments`
- `/deals`
- `/reports`
- `/news`
- `/search`
- `/ki`
- `/markt`
- `/pipeline`
- `/features`
- `/scheduler`

## PR721 Integration Status

Enterprise-reviewed and integrated from PR721:

- `pipeline` dashboard backed by real pipeline freshness and circuit-breaker data
- `features` dashboard backed by feature catalog, import validation, and quality reporting
- `search` connected to the existing semantic search API
- `ki` page converted into a real AI workspace with live backend status
- `markt` page connected to real market, news, and cooperative endpoints
- `scheduler` page connected to actual Celery beat jobs and task status
- additive provider catalog for weather, shipping, news, and macro sources
- additive models and safe Alembic `0020` migration for monitoring, sentiment, lineage, and feature cache tables

Not claimed in this README:

- no blanket "production ready" claim
- no fake coverage or endpoint counts
- no default credentials

## Local Start

### Prerequisites

- Docker Desktop
- Node.js 20+
- Python 3.11+ for local backend test runs

### Environment

Create a local `.env` from `.env.example` and set at least:

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- optional provider keys such as `PERPLEXITY_API_KEY` or `TAVILY_API_KEY`

For local dev admin bootstrap, `BOOTSTRAP_ADMIN_PASSWORD` must be set. The
bootstrap route is restricted to `dev` and `test`.

### Start with Docker

```bash
docker compose up --build
```

For workers and beat:

```bash
docker compose --profile workers up --build
```

Apply migrations:

```bash
docker compose exec backend alembic upgrade head
```

### Windows

For Windows-first local development, prefer:

- `run_windows.ps1`
- `README_WINDOWS.md`
- `docs/operations/windows.md`

## Verification Gates

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

## Architecture Notes

- API routes live in `apps/api/app/api/routes/`
- provider modules live in `apps/api/app/providers/`
- business logic lives in `apps/api/app/services/`
- PR721 compatibility facades were added under:
  - `apps/api/app/services/data_pipeline/phase2_orchestrator.py`
  - `apps/api/app/services/orchestration/phase4_scheduler.py`

## Key Docs

- `CODEBASE_MAP.md`
- `ENTERPRISE_ROADBOOK.md`
- `docs/operations/V0_SAFE_DELIVERY.md`
- `docs/operations/OPERATIONS_RUNBOOK.md`
- `docs/security/SECURITY.md`

## Security Notes

- Do not commit real `.env` values
- Dev bootstrap is disabled outside `dev` and `test`
- local secrets must be rotated per environment
- browser token handling has been hardened, but cookie auth is still the target end state
