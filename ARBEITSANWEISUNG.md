# Verbindliche Arbeitsanweisung — CoffeeStudio

> **Status:** verbindlich. Diese Datei ist die maßgebliche Quelle dafür, **wie** in
> diesem Repository gearbeitet wird (Mensch wie KI-Assistent). Bei Konflikten mit
> älteren Dokumenten gilt diese Anweisung. Inhaltliche Architektur-Details stehen
> in `CODEBASE_MAP.md` und `ENTERPRISE_ROADBOOK.md`.

---

## 1. Zweck & Geltung

- Diese Anweisung gilt für **alle** Änderungen am Repository.
- Sie ist **bindend**: Wer (oder was) hier arbeitet, hält sich an die Regeln in
  Abschnitt 9 (Verbote) und an die Qualitäts-Gates in Abschnitt 6, **bevor** ein
  PR zum Review gestellt wird.
- `CLAUDE.md` lädt diese Datei automatisch für den KI-Assistenten. `AI_INSTRUCTIONS.md`
  ist nur noch ein Verweis hierauf.

## 2. Architektur-Überblick (verifizierter Ist-Stand)

Monorepo mit zwei Anwendungen plus Infrastruktur.

| Bereich | Technologie |
| --- | --- |
| Frontend (`apps/web`) | Next.js 16 (App Router), TypeScript (strict), React Query |
| Backend (`apps/api`) | FastAPI, SQLAlchemy 2, Alembic, Pydantic v2 |
| Datenbank | PostgreSQL 16 (+ pgvector) |
| Cache / Queue | Redis 7, Celery, Celery Beat |
| Auth | JWT Bearer (Cookie-Migration vorbereitet) |
| Laufzeit | Docker Compose |

### Backend-Schichten (`apps/api/app/`)

- **Routen:** `app/domains/<domain>/api/routes.py` — aggregiert in `app/api/router.py`.
  > ⚠️ **Wichtig:** Es gibt **kein** `app/api/routes/` mehr. Frühere Compatibility-Wrapper
  > wurden entfernt. Ältere PR-/Doku-Verweise auf `app/api/routes/` oder `app/routes/`
  > sind veraltet.
- **Modelle:** `app/models/` (SQLAlchemy ORM).
- **Schemas:** `app/schemas/` (global) und `app/domains/<domain>/schemas/` (domänenlokal).
- **Business-Logik:** `app/services/` (geteilt) und vereinzelt `app/domains/<domain>/services/`.
- **Externe Integrationen:** ausschließlich `app/providers/`.
- **Querschnitt:** `app/core/` (config, security, audit, logging, error_handlers,
  validation, versioning, idempotency, export).
- **DB-Session:** `app/db/session.py`.
- **Middleware:** `app/middleware/` (Input-Validation, Security-Headers).
- **Async-Jobs:** `app/workers/` (Celery). **ML:** `app/ml/`, `app/services/ml/`.
- **Einstieg:** `app/main.py` (App-Factory, Middleware, Error-Handler, Startup-Seeding).

### Frontend-Schichten (`apps/web/`)

- **Routen/Seiten:** `app/<route>/page.tsx` (App Router).
- **Komponenten:** `app/components/`, Charts in `app/charts/`.
- **Daten-Hooks:** `app/hooks/` (React Query, zentrale `query-keys.ts`).
- **Service-Layer:** `app/services/` über den gemeinsamen Client `lib/api.ts`.
- **Typen:** `app/types/index.ts`. **Utils:** `app/utils/`.
- **Styles:** zentrales CSS-Designsystem in `app/globals.css` (CSS-Variablen).

## 3. Branch-, PR- & Commit-Regeln

- **Niemals direkt auf `main` oder `develop`** committen. Immer Feature-Branch + PR.
- **Branch-Namen:** `feature/<kurz>`, `fix/<kurz>`, `chore/<kurz>`, `refactor/<kurz>`,
  `docs/<kurz>`. KI-Branches: `claude/<kurz>`.
- **Kleine, fokussierte PRs.** Ein Thema pro PR. Mechanische Änderungen (z. B.
  Zeilenenden-Normalisierung) gehören in einen **eigenen** Commit, getrennt von
  logischen Änderungen.
- **Commit-Stil:** Conventional Commits, z. B.
  `feat(api): ...`, `fix(web): ...`, `refactor(api): ...`, `docs: ...`, `chore: ...`,
  `test(api): ...`, `ci: ...`.
- **PR erst nach grünen lokalen Gates** (Abschnitt 6). Keine PR-Erstellung „auf Verdacht".
- **Keine** internen Modell-IDs, Tokens oder Secrets in Commits, PR-Texten, Code-
  Kommentaren oder sonstigen versionierten Artefakten.

## 4. Backend-Regeln

- **Routen dünn halten:** validieren → Service rufen → Audit/Logging → Response.
  Orchestrierung gehört in Services, **nicht** in Route-Handler.
- **Typisierte Request-/Response-Modelle** verwenden (`response_model=...`), wo das
  umgebende Muster es vorgibt.
- **Externe Aufrufe** nur über `app/providers/`. Keine direkten HTTP-Clients in Routen/Services-Logik vermischen.
- **Config** ausschließlich über `app.core.config.settings` (Pydantic Settings). Keine
  `os.getenv`-Streuung. Feature-Flags dort pflegen.
- **Logging** strukturiert via `structlog` (`log = structlog.get_logger(...)`).
- **Auth/Rate-Limiting/Security-Middleware** nicht aushebeln. Rollen über
  `require_role(...)` / `get_current_user`.
- **Migrationen additiv:** Alembic in `apps/api/alembic/versions/`. Keine destruktiven
  Schema- oder Auth-Änderungen ohne ausdrücklichen Bedarf. Eine `down_revision`-Kette
  sauber halten (Merge-Heads vermeiden).

## 5. Frontend-Regeln

- **Datenzugriff** ausschließlich über `lib/api.ts` (`apiFetch`) bzw. die Service-/
  React-Query-Hooks. Keine rohen `fetch`-Aufrufe verstreuen.
- **Bestehende Muster wiederverwenden** (Hooks, `query-keys.ts`, Service-Layer).
- **Zustände immer behandeln:** Loading, Error, Empty — und Tastatur-/A11y-Zugang
  erhalten.
- **Echte Backend-Anbindung** bevorzugen. Demo-/Fallback-Daten klar als solche
  kennzeichnen; **keine** Fake-Live-Daten, die echt aussehen.
- **Styles** über das Designsystem in `globals.css` (CSS-Variablen). Inline-Styles
  vermeiden.

## 6. Qualitäts-Gates (verbindlich vor jedem PR)

**Backend** (`cd apps/api`):

```bash
python -m pytest -q                       # Tests grün
pytest --cov=app --cov-fail-under=70      # Coverage-Ziel 70 %
ruff format --check app tests             # Formatierung
ruff check app tests                      # Linting
mypy --config-file ../../mypy.ini app     # Typen
```

> Hinweis: Die Tests benötigen PostgreSQL (mit `pgvector`) und Redis. Coverage-Ausnahmen
> stehen in `apps/api/.coveragerc`. Das CI-Gate steht auf **70 %**.

**Frontend** (`cd apps/web`):

```bash
npm run lint
npm run build
```

**Compose** (Repo-Root):

```bash
docker compose config -q
docker compose -f docker-compose.stack.yml config -q
```

## 7. Sicherheit

- Secrets ausschließlich in lokaler `.env` (Vorlage: `.env.example`). **Nie** in
  versionierten Dateien.
- Dev-Bootstrap nur in `dev`/`test`. Default-Credentials niemals in Doku/Code.
- Browser-Token-Handling ist gehärtet; Cookie-Auth ist das Zielbild.
- Sicherheitslücken privat über GitHub Security Advisory melden (siehe `SECURITY.md`).

## 8. Doku- & Sprachpolitik

- **Code, Bezeichner, Commit-Messages, Code-Kommentare: Englisch.**
- **Diese Arbeitsanweisung und Endnutzer-Guides: Deutsch zulässig.** Bestehende
  englische technische Doku (`README.md`, `CODEBASE_MAP.md`) bleibt Englisch.
- Eine Information an **einer** kanonischen Stelle dokumentieren; Duplikate vermeiden.
  Veraltete Snapshots nach `docs/archive/` oder löschen.

## 9. Verbote / Non-Negotiables

- ❌ Bestehende Produktlogik beschädigen. **Erst schützen, dann ändern.**
- ❌ Destruktive Schema-/Auth-Änderungen ohne klaren Bedarf.
- ❌ Breite Rewrites statt additiver Adapter.
- ❌ „Production-ready" behaupten ohne echte Verifikation.
- ❌ Fake-Live-Daten in Dashboards.
- ❌ Secrets/Default-Credentials in versionierten Dateien.
- ❌ Doppelte Route-Bäume oder aufgeblähte Endpoint-/Coverage-Zahlen wieder einführen.
- ❌ Direkt auf `main`/`develop` pushen.

## 10. Standard-Workflow (Schritt für Schritt)

1. Von aktuellem `origin/main` (oder dem vorgegebenen Branch) starten.
2. Aufgabe in **kleinen Scheiben** umsetzen — eine Sache pro Commit.
3. Backend-Tests + Lint + Typen laufen lassen (Abschnitt 6).
4. Frontend-Lint + Build laufen lassen.
5. Compose-Validierung.
6. PR mit klarer Beschreibung erstellen; offene Punkte/Risiken benennen.
7. Erst nach grünen Gates eine Merge-Empfehlung aussprechen.

---

### Offene strukturelle Punkte (Folge-Arbeit, noch nicht erledigt)

Diese Punkte sind bewusst **nicht** Teil des ersten Cleanups und brauchen je eine
Entscheidung bzw. einen eigenen, abgesicherten PR:

- `app/qa/`: im Runtime ungenutztes, aber getestetes Subsystem (evtl. vom
  `qa-auto-fix`-Workflow verwendet) — entfernen oder offiziell integrieren?
- CI-Workflows konsolidieren und Trigger schärfen (`ruff-autofix` Auto-Commit-Risiko,
  `qa-auto-fix`, `synopsys` ohne Token; Überschneidungen Smoke/Monitoring/SAST).
- Tiefe Refactors: `app/services/discovery.py` (~1180 Z.) und `enrichment.py` (~960 Z.)
  in Submodule zerlegen; `apps/web/app/globals.css` modularisieren; XXL-Seiten
  (`shipments`, `markt`, `scheduler`, `assistant`) in Komponenten aufteilen; gemeinsamer
  `useListPage`-Hook; `ErrorState` → `AlertError` vereinheitlichen.
