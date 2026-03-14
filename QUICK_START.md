# CoffeeStudio Quick Start

## Ziel

Lokalen Stack starten, Migrationen anwenden und die integrierten PR721-Bereiche
verifizieren.

## Voraussetzungen

- Docker Desktop
- Node.js 20+
- Python 3.11+
- lokale `.env` mit `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`

## Start

```bash
docker compose up --build
docker compose --profile workers up --build
docker compose exec backend alembic upgrade head
```

## Wichtige URLs

- Frontend: `http://localhost:3000`
- API Health: `http://localhost:8000/health`
- API Docs: `http://localhost:8000/docs`

## Minimaler Verifikationslauf

```bash
pytest apps/api/tests/test_auth.py \
  apps/api/tests/test_rate_limiting.py \
  apps/api/tests/test_pr721_dashboard_routes.py \
  apps/api/tests/test_semantic_search.py \
  apps/api/tests/test_scheduler_dashboard_routes.py \
  apps/api/tests/test_market_dashboard_routes.py \
  apps/api/tests/test_monitoring_dashboard_routes.py -q
```

```bash
cd apps/web
npm run build
```
