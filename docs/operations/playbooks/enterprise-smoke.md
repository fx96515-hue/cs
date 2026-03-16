# Enterprise smoke test playbook

Purpose: quick, repeatable steps to validate the enterprise local stack (database, redis, backend, worker).

Prerequisites
- Docker & Docker Compose installed
- Copy `infra/env/enterprise.env.example` to `infra/env/enterprise.env` and adjust values as needed

Start the stack
```powershell
# from repo root
docker compose -f infra/deploy/docker-compose.enterprise.yml up --build -d

# Wait for services to be healthy (inspect logs if needed):
docker compose -f infra/deploy/docker-compose.enterprise.yml ps
docker compose -f infra/deploy/docker-compose.enterprise.yml logs -f backend
```

Run smoke checks
```powershell
# Basic health endpoint (FastAPI exposes /health or /metrics):
curl http://localhost:8000/health

# Run backend pytest smoke subset (if available):
pytest -q apps/api/tests -k smoke
```

Common fixes
- If Postgres fails to initialize: remove old volumes or check env values in `infra/env/enterprise.env`.
- If pgvector is required and not present, either install the extension locally in the DB image or set provider fallbacks.

Teardown
```powershell
docker compose -f infra/deploy/docker-compose.enterprise.yml down -v
```

If you'd like, I can add a `Makefile` target or `scripts/start_enterprise.ps1` wrapper to make these commands one-liners.
