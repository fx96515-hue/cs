PYTHON ?= python3
ENTERPRISE_COMPOSE ?= infra/deploy/docker-compose.enterprise.yml

.PHONY: help up down logs status migrate bootstrap smoke smoke-win \
        start-enterprise stop-enterprise enterprise-logs enterprise-status enterprise-restart

help:
	@echo "CoffeeStudio Platform — common targets"
	@echo ""
	@echo "Dev stack:"
	@echo "  make up            # docker compose up -d --build"
	@echo "  make down          # docker compose down"
	@echo "  make logs          # follow logs (dev)"
	@echo "  make status        # docker compose ps"
	@echo "  make migrate       # alembic upgrade head (in backend container)"
	@echo "  make bootstrap     # seed dev admin (requires backend running)"
	@echo "  make smoke         # run smoke flow against running dev stack"
	@echo "  make smoke-win     # run smoke (Windows)"
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
