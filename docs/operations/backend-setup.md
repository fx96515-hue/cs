# Backend Setup

This guide is the stable backend quickstart for local development and validation.

## Scope

- API service (`apps/api`)
- Postgres and Redis runtime dependencies
- Celery worker and beat process
- migrations and smoke checks

## Prerequisites

- Docker Desktop (or Docker Engine + Compose)
- Python 3.11+ (only needed for local non-container test runs)
- A local `.env` file based on `.env.example`

## Required Environment Variables

Set at least these values in `.env`:

```env
DATABASE_URL=postgresql+psycopg://coffeestudio:coffeestudio@postgres:5432/coffeestudio
REDIS_URL=redis://redis:6379/0
JWT_SECRET=<set-a-strong-secret>
BOOTSTRAP_ADMIN_EMAIL=admin@coffeestudio.com
BOOTSTRAP_ADMIN_PASSWORD=<set-a-strong-password>
```

Notes:

- Do not commit real secrets.
- Do not use placeholder defaults in shared environments.
- For local dev bootstrap, backend bootstrap routes are environment-gated and host-restricted.

## Start Local Stack

```bash
docker compose up -d --build
```

Start including worker profile:

```bash
docker compose --profile workers up -d --build
```

## Apply Migrations

```bash
docker compose exec backend alembic upgrade head
```

## Health and Smoke Checks

Backend health:

```bash
curl http://localhost:8000/health
```

Windows smoke:

```powershell
powershell -File scripts/win/smoke.ps1
```

Expected smoke result: all gates passed.

## Backend Quality Gates

Run from `apps/api`:

```bash
python -m pytest -q
ruff check app tests
mypy --config-file ../../mypy.ini app
```

## Troubleshooting

Backend container not healthy:

1. Check container status: `docker compose ps`
2. Check logs: `docker compose logs backend --tail=200`
3. Verify env values in `.env` (DB/Redis/JWT)
4. Rebuild cleanly if needed: `docker compose build --no-cache backend`

Migration failures:

1. Verify DB container is healthy before running Alembic
2. Review `docker compose logs backend`
3. If local state is broken, recreate local volumes only when appropriate:
   `docker compose down -v && docker compose up -d --build`

## Repo and Docker Cleanup

Use the maintenance script for repeatable local cleanup:

```powershell
# show what would be removed
powershell -ExecutionPolicy Bypass -File scripts/maintenance/cleanup_local_artifacts.ps1

# apply local repo artifact cleanup
powershell -ExecutionPolicy Bypass -File scripts/maintenance/cleanup_local_artifacts.ps1 -Apply

# apply cleanup including Docker image/cache prune
powershell -ExecutionPolicy Bypass -File scripts/maintenance/cleanup_local_artifacts.ps1 -Apply -DockerPrune
```

Equivalent `make` targets:

```bash
make cleanup-local
make cleanup-local-apply
make cleanup-local-docker
```

## Related Docs

- `README.md`
- `README_WINDOWS.md`
- `docs/operations/enterprise-quickstart.md`
- `docs/operations/OPERATIONS_RUNBOOK.md`
- `docs/security/SECURITY.md`
