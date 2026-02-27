# Deploy (Enterprise) — Local Docker Compose

This guide shows how to run a production-like stack locally using the **enterprise** docker-compose.

Key files
- `infra/deploy/docker-compose.enterprise.yml`
- `infra/env/enterprise.env.example` (example)
- `infra/env/enterprise.env` (local, not committed)

Prerequisites
- Docker and Docker Compose installed
- Sufficient disk space for Postgres image

Quick start

1) Review the example env and create your local enterprise env (recommended):

```bash
cp infra/env/enterprise.env.example infra/env/enterprise.env
# Edit infra/env/enterprise.env and set a strong JWT_SECRET and PERPLEXITY_API_KEY if needed
```

> Note: `infra/env/enterprise.env` is ignored by git (see `.gitignore`).

2) Start the stack:

```bash
docker compose -f infra/deploy/docker-compose.enterprise.yml up --build -d
```

3) Run migrations and seed data (inside backend container):

```bash
docker compose -f infra/deploy/docker-compose.enterprise.yml exec backend alembic upgrade head
curl -s -X POST http://localhost:8000/auth/dev/bootstrap | cat
```

4) Verify health:

```bash
curl -fsS http://localhost:8000/health | cat
```

Stop / cleanup

```bash
docker compose -f infra/deploy/docker-compose.enterprise.yml down -v
```
