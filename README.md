# CoffeeStudio Platform (Option D) — Web-App + API + DB

Dieses Repository ist ein **produktreifes Foundation-Setup** für CoffeeStudio (Peru → Deutschland Specialty Coffee).

[![Coverage](https://img.shields.io/badge/coverage-75%25-yellowgreen)](https://github.com/fx96515-hue/coffeestudio-platform/actions)
[![Codecov](https://img.shields.io/badge/codecov-xml-blue)](https://codecov.io/gh/fx96515-hue/coffeestudio-platform)
[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-white.svg)](https://sonarcloud.io/summary/new_code?id=fx96515-hue_coffeestudio-platform)

Notes:
- The Codecov and SonarCloud badges are placeholders — configure `CODECOV_TOKEN` and `SONAR_TOKEN` in GitHub repository secrets to enable uploads.

**Stack**
- **Backend API:** FastAPI (Python)
- **DB:** Postgres
- **Cache/Broker:** Redis
- **Worker/Scheduler:** Celery + Celery Beat
- **Frontend:** Next.js (App Router) + TypeScript

## Kernfunktionen (v0.2.1c)
- CRUD für **Kooperativen** und **Röster**
- CRUD für **Lots** (lot-/shipment-orientierte Stammdaten)
- **Margen-Engine** (Calc + gespeicherte Runs je Lot)
- **Auth (JWT)** + einfache **RBAC-Rollen** (admin/analyst/viewer)
- **Quelle/Provenance**: jede Kennzahl kann mit Source + Timestamp gespeichert werden
- **Scoring Engine (v0):** Qualität/Zuverlässigkeit/Wirtschaftlichkeit + Confidence
- **Market Data (v0):** FX (ECB) Beispiel-Provider, Provider-Interface für Kaffee/Fracht
- **Daily Report (v0):** Report-Entität + Generator (API + Worker)

## UI (Next.js)
- Listen/Details: Kooperativen, Röster
- **Lots**: Liste + anlegen + Detail + Margen-Runs speichern
- **Reports**: Liste + Detail (Markdown-Rendering)

## Quickstart (Dev)

> **Windows 11 (PowerShell) empfohlen:** siehe `README_WINDOWS.md` oder direkt `run_windows.ps1` ausführen.

### 1) Voraussetzungen
- Docker + Docker Compose

### 2) Starten
```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000/docs

### 3) Erster Admin-User

1) Migration:
```bash
docker compose exec backend alembic upgrade head
```
2) Dev-Bootstrap (legt admin@coffeestudio.com / adminadmin an, wenn DB leer ist):
```bash
curl -X POST http://localhost:8000/auth/dev/bootstrap
```

## Perplexity Discovery Seed (Kooperativen + Röster)

Wenn du `PERPLEXITY_API_KEY` setzt, kann CoffeeStudio ein **Start-Set** an Einträgen automatisch finden
und als Tasks/Einträge in der DB anlegen (jeweils mit **Evidence-URLs** in `entity_evidence`).

**Wichtig:** Das ist bewusst **konservativ** – wir füllen primär leere Felder und markieren `next_action = "In Recherche"`.

### Variante A: per API (asynchron via Celery)

1) `PERPLEXITY_API_KEY` in `.env` setzen
2) Stack starten + migrieren
3) Seed-Job anstoßen:

```bash
curl -X POST http://localhost:8000/discovery/seed \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"entity_type":"both","max_entities":50,"dry_run":false}'
```

Status abfragen:

```bash
curl http://localhost:8000/discovery/seed/<TASK_ID> \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### Variante B: per Script (synchron)

```bash
docker compose exec backend python scripts/seed_first_run.py --both --max 50
```

### Smoke-Test

```bash
make smoke
```

## Architektur
- `apps/api/` FastAPI + DB + Domain-Services
- `worker/` Celery Worker/Beat (nutzt denselben Python-Code wie backend)
- `apps/web/` Next.js UI
- `infra/` optionale Deploy-Assets

## CI/CD Pipeline

Production-ready CI/CD pipeline with GitHub Actions:

✅ **Automated Testing** - Backend & frontend tests on every PR  
✅ **Security Scans** - Bandit, Trivy, CodeQL, Semgrep  
✅ **Docker Build** - Multi-platform images pushed to GHCR  
✅ **Staging Deploy** - Auto-deploy on `develop` branch  
✅ **Production Deploy** - Manual approval with auto-rollback  
✅ **Monitoring** - Post-deployment health checks & alerts

📚 **[Complete CI/CD Documentation](.github/workflows/README.md)**  
🔐 **[Secrets Setup Guide](.github/workflows/SECRETS_SETUP.md)**

**Pipeline Status:**
- [![CI Pipeline](https://github.com/fx96515-hue/coffeestudio-platform/workflows/CI%20Pipeline/badge.svg)](https://github.com/fx96515-hue/coffeestudio-platform/actions/workflows/ci.yml)
- Execution Time: ~12-15 minutes (parallel)
- Test Coverage: Backend 57%+, Frontend configured

## Sicherheit (Foundation)
- JWT via `Authorization: Bearer ...`
- Passwörter gehasht (`pbkdf2_sha256`)
- CORS restriktiv konfigurierbar
- Rate Limiting (SlowAPI)
- Input validation (Pydantic)
- **Security Headers Middleware** (X-Frame-Options, CSP, HSTS, etc.)
- **Input Validation Middleware** (SQL Injection & XSS Detection)
- **Standardized Error Handling** with consistent error format

See [SECURITY.md](docs/security/SECURITY.md) and [SECURITY_BEST_PRACTICES.md](docs/security/SECURITY_BEST_PRACTICES.md) for comprehensive security documentation.

## API Documentation

📖 **See [API_USAGE_GUIDE.md](./docs/guides/API_USAGE_GUIDE.md)** for:
- Complete API reference with examples
- Authentication & authorization guide
- Request/response formats
- Error handling
- Rate limiting details
- Python & JavaScript SDK examples

Interactive API docs available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Testing

Comprehensive test suite with **45 passing tests** and **57% code coverage**.

### Backend Tests

```bash
cd apps/api
pip install -r requirements-dev.txt
pytest tests/ -v
```

**With coverage:**
```bash
pytest tests/ --cov=app --cov-report=html
```

See [TESTING.md](docs/guides/TESTING.md) for complete testing documentation.

### Security

See [SECURITY.md](docs/security/SECURITY.md) and [SECURITY_BEST_PRACTICES.md](docs/security/SECURITY_BEST_PRACTICES.md) for comprehensive security documentation.

## Status & Roadmap

📊 **Siehe [STATUS.md](./docs/operations/STATUS.md)** für:
- Aktueller Status aller Features
- Was kommt als Nächstes (4-Phasen-Roadmap)
- Implementation Backlog
- Vorschläge & Empfehlungen
- Produktivsetzung (Production Readiness: 60%)

## 📚 Documentation

Complete documentation is organized in the [docs/](docs/) directory:

- **[Architecture & Implementation](docs/architecture/)** - System design and technical summaries
- **[Guides & Quick Starts](docs/guides/)** - Step-by-step guides and tutorials
- **[Security](docs/security/)** - Security policies and best practices
- **[Operations](docs/operations/)** - Runbooks and status reports

## Nächste Schritte
- Vollständige Provider (ICO/ICE/Fracht)
- Multi-Tenant / Mandantenfähigkeit (optional)
- Fine-grained Permissions + Audit Log
- CI/CD + Container Registry + Deployment
