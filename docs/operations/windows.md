# CoffeeStudio OptionD — Windows Runbook (Docker Desktop)

Zeitzone: Europe/Berlin

## Voraussetzungen
- Windows 11 + Docker Desktop (WSL2 Backend)
- PowerShell 7+ empfohlen (Windows PowerShell 5 geht i.d.R. auch)

## Quickstart
```powershell
cd <deinPfad>\coffeestudio-platform
.\run_windows.ps1
```

Das Script:
- legt bei Bedarf `.env` aus `.env.example` an
- generiert lokal ein `JWT_SECRET`
- setzt für DEV einen Bootstrap-Admin (Email+Passwort)
- startet Compose + Migrationen + Bootstrap

UI: http://localhost:3000  
API: http://localhost:8000/docs

---

## App-Style Stack (Domains via Traefik)

Wenn du das Ganze wie eine "echte" App nutzen willst (ein Einstiegspunkt, saubere URLs, optionale Ops-/BI-Tools), nutze den Stack-Modus.

### 1) Lokale Domains eintragen (one-time)

PowerShell als Administrator:

```powershell
cd <deinPfad>\coffeestudio-platform
.\scripts\win\01_add_hosts.ps1
```

Das trägt folgende Domains in die HOSTS-Datei ein (127.0.0.1):
`ui.localhost`, `api.localhost`, `traefik.localhost`, `ops.localhost`, `bi.localhost`, `docker.localhost`, `auth.localhost`, `app.localhost`.

### 2) Stack starten

```powershell
cd <deinPfad>\coffeestudio-platform
.\scripts\win\02_stack_up.ps1
```

### 3) URLs

- UI: http://ui.localhost
- API Health: http://api.localhost/health
- Traefik Dashboard: http://traefik.localhost/dashboard/

Hinweis: Im Stack-Modus läuft alles über Traefik auf Port 80. Viele Services publishen dann **keine** eigenen Ports (sauberer, wie Produktion).

---

## Gates (Copy/Paste)

### Gate 0 — Verzeichnis
```powershell
Test-Path .\docker-compose.yml
```
**Expected:** `True`

### Gate 1 — Compose up
```powershell
docker compose up -d --build
docker compose ps
```
**Expected:** services `Up`, `postgres`/`redis` healthy, `backend` healthy.

### Gate 2 — Backend health
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
```
**Expected:** `{"status":"ok"}`

### Gate 3 — DB migrations
```powershell
docker compose exec backend alembic upgrade head
```
**Expected:** `0 errors`

### Gate 4 — Dev bootstrap
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/dev/bootstrap"
docker compose exec postgres psql -U coffeestudio -d coffeestudio -c "select id, email, role, is_active from users order by id;"
```
**Expected:** `status=created` (erstes Mal), danach `status=skipped`. User ist in DB.

### Gate 5 — Login (JWT Token)
```powershell
$body = @{ email="admin@coffeestudio.com"; password="adminadmin" } | ConvertTo-Json
$token = (Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/login" -ContentType "application/json" -Body $body).access_token
$token
```
**Expected:** JWT string.

### Gate 6 — Authenticated API (kein 401)
```powershell
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://localhost:8000/cooperatives" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/roasters" -Headers $headers
```
**Expected:** 200 + payload.

### Gate 7 — Seed dry-run
```powershell
docker compose exec backend python scripts/seed_first_run.py --both --max 50 --dry-run
```
**Expected:** `created>0`, `errors=[]`

### Gate 8 — Seed write
```powershell
docker compose exec backend python scripts/seed_first_run.py --both --max 50

docker compose exec postgres psql -U coffeestudio -d coffeestudio -c "select count(*) from cooperatives; select count(*) from roasters;"
```
**Expected:** counts > 0.

### Gate 9 — Frontend
Open: http://localhost:3000

---

## Optional Data-Gates (neue Data-Backbone Features)

### Data Gate A — Peru Regionen KB seed + list
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/regions/peru/seed" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/regions/peru" -Headers $headers
```

### Data Gate B — News refresh + list
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/news/refresh?topic=peru%20coffee&country=PE&max_items=25" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/news?topic=peru%20coffee&limit=20&days=14" -Headers $headers
```

### Data Gate C — Dedup suggestions
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/dedup/suggest?entity_type=cooperative&threshold=90&limit=10" -Headers $headers
```

### Data Gate D — Landed-cost calculator
```powershell
$payload = @{ weight_kg=69; green_price_usd_per_kg=6.5; incoterm="FOB"; freight_usd=1200; handling_eur=180 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/logistics/landed-cost" -Headers $headers -ContentType "application/json" -Body $payload
```

### Data Gate E — Outreach text
```powershell
$payload = @{ entity_type="roaster"; entity_id=1; language="de"; purpose="sourcing_pitch"; refine_with_llm=$false } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/outreach/generate" -Headers $headers -ContentType "application/json" -Body $payload
```

### Data Gate F — KB seed + list
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/kb/seed" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/kb?category=logistics&language=de" -Headers $headers
```

### Data Gate G — Cupping create + list
```powershell
$payload = @{ cooperative_id=1; sca_score=86.25; descriptors="citrus, cacao"; notes="Sample roasting (test)" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/cuppings" -Headers $headers -ContentType "application/json" -Body $payload
Invoke-RestMethod -Uri "http://localhost:8000/cuppings?limit=5" -Headers $headers
```

---

## Troubleshooting (Standard)
- Logs:
```powershell
docker compose logs --tail 200 backend
docker compose logs --tail 200 frontend
docker compose logs --tail 200 worker
```
- ENV Check im Container:
```powershell
docker compose exec backend bash -lc "python - << 'PY'
import os
print('BOOTSTRAP_ADMIN_EMAIL=', os.getenv('BOOTSTRAP_ADMIN_EMAIL'))
print('BOOTSTRAP_ADMIN_PASSWORD length=', len(os.getenv('BOOTSTRAP_ADMIN_PASSWORD') or ''))
print('JWT_SECRET set=', bool(os.getenv('JWT_SECRET')))
print('PERPLEXITY_API_KEY set=', bool(os.getenv('PERPLEXITY_API_KEY')))
PY"
```
