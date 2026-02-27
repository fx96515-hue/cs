# Deploy (Enterprise) — Local Docker Compose

This guide shows how to run a production-like stack locally using the enterprise docker-compose.

Files added
- `ops/deploy/docker-compose.enterprise.yml`
- `.env.enterprise.example`

Prerequisites
- Docker and Docker Compose installed
- Sufficient disk space for Postgres image

Quick start

1. Copy the example env and set secrets:

```bash
cp .env.enterprise.example .env.enterprise
# Edit .env.enterprise and set a strong JWT_SECRET and PERPLEXITY_API_KEY if needed
```

2. Start the stack:

```bash
cd ops/deploy
docker compose -f docker-compose.enterprise.yml up --build -d
```

3. Run migrations and seed data (inside backend container):

```bash
docker compose -f docker-compose.enterprise.yml exec backend alembic upgrade head
# Optionally run startup seed via CLI or ensure startup event seeds data
```

4. Visit the API:
- Backend: http://localhost:8000
- Prometheus (if running external): http://localhost:9090
- Grafana (if running): http://localhost:3000

Notes
- The `backend` service uses the repo `apps/api/Dockerfile`. Ensure the Dockerfile exposes port 8000 and installs required packages.
- For production, replace `postgres` image and secrets with managed services and secure the `JWT_SECRET` and other keys.
