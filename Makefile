PYTHON ?= python3
ENTERPRISE_COMPOSE ?= infra/deploy/docker-compose.enterprise.yml

.PHONY: help up up-full down logs status migrate bootstrap smoke smoke-win \
        start-enterprise stop-enterprise enterprise-logs enterprise-status enterprise-restart \
        cleanup-local cleanup-local-apply cleanup-local-docker \
        dev-services dev-services-down dev-setup dev-migrate dev-bootstrap dev-api dev-web

help:
	@echo "CoffeeStudio Platform — common targets"
	@echo ""
	@echo "Dev stack:"
	@echo "  make up            # docker compose up -d --build (core services)"
	@echo "  make up-full       # docker compose --profile workers up -d --build"
	@echo "  make down          # docker compose down"
	@echo "  make logs          # follow logs (dev)"
	@echo "  make status        # docker compose ps"
	@echo "  make migrate       # alembic upgrade head (in backend container)"
	@echo "  make bootstrap     # seed dev admin (requires backend running)"
	@echo "  make smoke         # run smoke flow against running dev stack"
	@echo "  make smoke-win     # run smoke (Windows)"
	@echo ""
	@echo "Local dev (no Docker for app code — see LOCAL_DEV.md):"
	@echo "  make dev-services  # start ONLY postgres(pgvector)+redis in docker (optional)"
	@echo "  make dev-setup     # venv + deps + web install + migrate + admin"
	@echo "  make dev-api       # uvicorn with --reload on :8000"
	@echo "  make dev-web       # next dev on :3000"
	@echo ""
	@echo "Enterprise stack:"
	@echo "  make start-enterprise        # start enterprise compose + health checks"
	@echo "  make stop-enterprise         # stop enterprise compose (with volumes)"
	@echo "  make enterprise-logs         # follow enterprise logs"
	@echo "  make enterprise-status       # enterprise docker compose ps"
	@echo "  make enterprise-restart      # restart enterprise stack"
	@echo ""
	@echo "Vars:"
	@echo "  ENTERPRISE_COMPOSE=$(ENTERPRISE_COMPOSE)"

# -----------------------
# Dev stack (docker-compose.yml)
# -----------------------
up:
	docker compose up -d --build

up-full:
	docker compose --profile workers up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

status:
	docker compose ps

migrate:
	docker compose exec backend alembic upgrade head

bootstrap:
	curl -s -X POST http://localhost:8000/auth/dev/bootstrap | cat

smoke:
	bash scripts/smoke.sh

smoke-win:
	powershell -ExecutionPolicy Bypass -File scripts/win/smoke.ps1

# -----------------------
# Local dev without Docker (run API + web natively; see LOCAL_DEV.md)
# -----------------------
# Optional: run just the two stateful services in containers; the app code runs
# natively with hot reload. Skip these if you already have local Postgres+Redis.
DEV_PGVECTOR_IMAGE ?= pgvector/pgvector:pg16
# Override these to run alongside another local project (e.g. Trade Desk) without
# port clashes: `make dev-api API_PORT=8001`, `make dev-services PG_PORT=5433`, …
API_PORT ?= 8000
WEB_PORT ?= 3000
PG_PORT ?= 5432
REDIS_PORT ?= 6379

dev-services:
	docker run -d --name obee-pg -p $(PG_PORT):5432 \
		-e POSTGRES_DB=coffeestudio -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
		$(DEV_PGVECTOR_IMAGE) || docker start obee-pg
	docker run -d --name obee-redis -p $(REDIS_PORT):6379 redis:7 || docker start obee-redis

dev-services-down:
	-docker rm -f obee-pg obee-redis

dev-setup:
	cd apps/api && $(PYTHON) -m venv .venv && . .venv/bin/activate && \
		pip install -r requirements.txt -r requirements-dev.txt && alembic upgrade head
	cd apps/web && npm install
	$(MAKE) dev-bootstrap

dev-migrate:
	cd apps/api && . .venv/bin/activate && alembic upgrade head

dev-bootstrap:
	curl -s -X POST http://localhost:$(API_PORT)/auth/dev/bootstrap | cat || true

dev-api:
	cd apps/api && . .venv/bin/activate && \
		uvicorn app.main:app --reload --host 127.0.0.1 --port $(API_PORT)

dev-web:
	cd apps/web && NEXT_PUBLIC_API_URL=http://localhost:$(API_PORT) npm run dev -- -p $(WEB_PORT)

# -----------------------
# Enterprise stack (infra/deploy/docker-compose.enterprise.yml)
# -----------------------
start-enterprise:
	@echo "Start enterprise stack (powershell: .\\scripts\\start_enterprise.ps1 -action start)"
	chmod +x scripts/ci_start_enterprise.sh || true
	./scripts/ci_start_enterprise.sh "$(ENTERPRISE_COMPOSE)" "http://localhost:8000/health"

stop-enterprise:
	docker compose -f "$(ENTERPRISE_COMPOSE)" down -v

enterprise-logs:
	docker compose -f "$(ENTERPRISE_COMPOSE)" logs -f

enterprise-status:
	docker compose -f "$(ENTERPRISE_COMPOSE)" ps

enterprise-restart:
	$(MAKE) stop-enterprise
	$(MAKE) start-enterprise

# -----------------------
# Local hygiene / cleanup
# -----------------------
cleanup-local:
	powershell -ExecutionPolicy Bypass -File scripts/maintenance/cleanup_local_artifacts.ps1

cleanup-local-apply:
	powershell -ExecutionPolicy Bypass -File scripts/maintenance/cleanup_local_artifacts.ps1 -Apply

cleanup-local-docker:
	powershell -ExecutionPolicy Bypass -File scripts/maintenance/cleanup_local_artifacts.ps1 -Apply -DockerPrune
