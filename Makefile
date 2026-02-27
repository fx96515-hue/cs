PYTHON ?= python3

.PHONY: start-enterprise stop-enterprise logs status smoke

start-enterprise:
	@echo "Start enterprise stack (powershell: .\\scripts\\start_enterprise.ps1 -action start)"
	chmod +x scripts/ci_start_enterprise.sh || true
	./scripts/ci_start_enterprise.sh

stop-enterprise:
	@docker compose -f ops/deploy/docker-compose.enterprise.yml down -v

logs:
	@docker compose -f ops/deploy/docker-compose.enterprise.yml logs -f

status:
	@docker compose -f ops/deploy/docker-compose.enterprise.yml ps

smoke:
	@$(PYTHON) -m pip install -r backend/requirements.txt
	@pip install pytest pytest-asyncio
	@pytest -q backend/tests -k smoke
.PHONY: up down logs migrate bootstrap smoke smoke-win

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose exec backend alembic upgrade head

bootstrap:
	curl -s -X POST http://localhost:8000/auth/dev/bootstrap | cat

smoke:
	bash scripts/smoke.sh

smoke-win:
	powershell -ExecutionPolicy Bypass -File scripts/win/smoke.ps1
