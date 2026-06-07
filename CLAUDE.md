# CLAUDE.md

This file is loaded automatically by Claude Code. The **binding** work instruction
for this repository is **[`ARBEITSANWEISUNG.md`](ARBEITSANWEISUNG.md)** (German).
Read it before making changes. The most critical rules are summarized below.

## Must-know facts

- Monorepo: `apps/api` (FastAPI + SQLAlchemy + Alembic + Pydantic) and
  `apps/web` (Next.js 16 App Router + TypeScript + React Query).
- **Backend routes live in `app/domains/<domain>/api/routes.py`**, aggregated in
  `app/api/router.py`. There is **no** `app/api/routes/` directory (legacy wrappers
  were removed). Ignore older references to `app/api/routes/` or `app/routes/`.
- External integrations go behind `app/providers/`. Config only via
  `app.core.config.settings`. Logging via `structlog`.
- Frontend data access only via `lib/api.ts` / React Query hooks.

## Hard rules

- Never commit directly to `main`/`develop` — always a feature branch + PR.
- Keep routes thin; orchestration belongs in services.
- Migrations are additive only; no destructive schema/auth changes without clear need.
- Secrets only in local `.env`; never in tracked files. No fake "live" dashboard data.
- Keep mechanical changes (e.g. line-ending normalization) in their own commit.

## Quality gates before any PR

Backend (`cd apps/api`):

```bash
python -m pytest -q
pytest --cov=app --cov-fail-under=70
ruff format --check app tests && ruff check app tests
mypy --config-file ../../mypy.ini app
```

Frontend (`cd apps/web`): `npm run lint && npm run build`

Compose (root): `docker compose config -q`

> Backend tests require PostgreSQL (with `pgvector`) and Redis.

See `ARBEITSANWEISUNG.md` for the full, authoritative rules, the architecture map,
and the list of open structural follow-ups.
