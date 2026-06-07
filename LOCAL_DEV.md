# Local development without Docker

You don't need the full Docker stack to develop. Only **PostgreSQL (with
pgvector)** and **Redis** need to run as services — the API and the web app run
natively with hot reload. This is the fastest inner loop.

> Binding rules: see [`ARBEITSANWEISUNG.md`](ARBEITSANWEISUNG.md).

## TL;DR

```bash
# 1. Stateful services (pick ONE)
make dev-services                 # runs ONLY postgres(pgvector)+redis in docker
#   …or use your own local Postgres+Redis and skip this.

# 2. One-time setup (venv, deps, web install, migrate, seed admin)
make dev-setup

# 3. Run the two apps in two terminals
make dev-api                      # FastAPI on http://localhost:8000 (--reload)
make dev-web                      # Next.js on http://localhost:3000
```

API health check: `curl http://localhost:8000/health` → `{"status":"ok"}`.

## Configuration

Copy the example env and adjust as needed:

```bash
cp .env.example apps/api/.env
```

Minimum for local dev (`apps/api/.env`):

```ini
APP_ENV=dev
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/coffeestudio
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=local_dev_secret_key_minimum_32_characters_long_ok
CORS_ORIGINS=http://localhost:3000
BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_PASSWORD=ChangeMe_12345
```

The web app reads `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000` via
`make dev-web`).

## Running alongside another local project (avoid port clashes)

Everything binds to `localhost` (same IP), so projects are separated by **port**,
not IP. If another app (e.g. Trade Desk) already uses 8000/3000/5432/6379, run
CoffeeStudio on different ports — the targets take overrides:

```bash
make dev-services PG_PORT=5433 REDIS_PORT=6380
make dev-api      API_PORT=8001
make dev-web      API_PORT=8001 WEB_PORT=3001
```

Then point `apps/api/.env` at the same ports:

```ini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/coffeestudio
REDIS_URL=redis://localhost:6380/0
CORS_ORIGINS=http://localhost:3001
```

(The two apps can also simply run one at a time — then defaults are fine.)

## Why no Docker for the app code?

- **Faster reloads:** `uvicorn --reload` and `next dev` rebuild on save without
  rebuilding images.
- **Lean:** only the two stateful services need to exist; everything else is
  plain `python` / `node`.
- The Docker stack (`make up`) is still there for full-stack / parity runs and
  for CI.

## Optional extras

- **Workers (Celery):** `cd apps/api && . .venv/bin/activate && celery -A app.workers.celery_app worker -l info`
- **AI features** (assistant, RAG, enrichment) need provider keys in
  `apps/api/.env` (e.g. `OPENAI_API_KEY`, `PERPLEXITY_API_KEY`); without them
  those endpoints report unavailable but the rest of the app works.
- **Obee extension:** see [`apps/extension/README.md`](apps/extension/README.md);
  it talks to this local API at `http://localhost:8000`.

## Quality gates (run before a PR)

```bash
cd apps/api && . .venv/bin/activate
pytest -q && ruff format --check app tests && ruff check app tests && mypy --config-file ../../mypy.ini app
cd ../web && npm run lint && npm run build
```
