# CoffeeStudio Platform - Operations Runbook

## 🚀 Quick Links
- **Health Check:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs
- **Metrics:** http://localhost:8000/metrics
- **Grafana:** http://ops.localhost (Stack-Modus)
- **Prometheus:** http://prom.localhost (Stack-Modus)

## 📊 Service Status

### Health Checks
```bash
# Backend
curl -f http://localhost:8000/health || echo "Backend DOWN"

# Database
docker compose exec postgres pg_isready -U coffeestudio || echo "DB DOWN"

# Redis
docker compose exec redis redis-cli ping || echo "Redis DOWN"

# Celery Worker
docker compose exec worker celery -A app.workers.celery_app.celery inspect ping || echo "Worker DOWN"
```

### Logs anzeigen
```bash
# Backend (letzte 100 Zeilen)
docker compose logs --tail 100 -f backend

# Alle Services
docker compose logs -f

# Errors filtern
docker compose logs backend | grep -i error

# Worker-Tasks tracken
docker compose logs worker | grep -i "Task"
```

## 🚨 Troubleshooting

### Problem: Backend startet nicht

**Symptome:**
- `docker compose ps` zeigt backend als "unhealthy" oder "restarting"
- Health-Check schlägt fehl

**Diagnose:**
```bash
# 1. Container-Status prüfen
docker compose ps

# 2. Logs checken
docker compose logs --tail 200 backend

# 3. Häufige Ursachen:
# - DB-Migration fehlgeschlagen
# - Fehlende Umgebungsvariablen
# - Port-Konflikt
```

**Lösung:**
```bash
# DB-Migrations-Status prüfen
docker compose exec backend alembic current

# Migrations manuell ausführen
docker compose exec backend alembic upgrade head

# Container neu starten
docker compose restart backend

# Falls hartnäckig: Rebuild
docker compose up -d --build backend
```

---

### Problem: Datenbank-Verbindungsfehler

**Symptome:**
- Backend-Logs: "could not connect to server"
- API gibt 500er zurück

**Diagnose:**
```bash
# DB-Container läuft?
docker compose ps postgres

# DB ist erreichbar?
docker compose exec postgres pg_isready -U coffeestudio -d coffeestudio

# Netzwerk OK?
docker compose exec backend ping postgres
```

**Lösung:**
```bash
# Postgres neu starten
docker compose restart postgres

# Warten bis healthy (max 30s)
timeout 30 bash -c 'until docker compose exec postgres pg_isready; do sleep 1; done'

# Backend neu starten (nutzt neue Connection)
docker compose restart backend
```

---

### Problem: Frontend zeigt "API nicht erreichbar"

**Symptome:**
- UI lädt, aber API-Calls schlagen fehl
- Browser-Console: CORS-Fehler oder Network Error

**Diagnose:**
```bash
# Backend erreichbar?
curl http://localhost:8000/health

# CORS-Config prüfen
docker compose exec backend env | grep CORS_ORIGINS

# Netzwerk OK?
docker compose exec frontend ping backend
```

**Lösung:**
```bash
# Prüfe .env:
# CORS_ORIGINS=http://localhost:3000
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Falls im Stack-Modus (Traefik):
# CORS_ORIGINS=http://ui.localhost
# NEXT_PUBLIC_API_URL=http://api.localhost

# Neu starten
docker compose restart frontend backend
```

---

### Problem: Celery-Worker verarbeitet keine Tasks

**Symptome:**
- Tasks bleiben in "PENDING"
- Worker-Logs zeigen keine Aktivität

**Diagnose:**
```bash
# Worker läuft?
docker compose ps worker

# Redis erreichbar?
docker compose exec worker redis-cli -h redis ping

# Tasks in Queue?
docker compose exec redis redis-cli -h redis LLEN celery

# Worker-Status
docker compose exec worker celery -A app.workers.celery_app.celery inspect active
```

**Lösung:**
```bash
# Worker neu starten
docker compose restart worker

# Celery Beat (Scheduler) auch neu starten
docker compose restart beat

# Tasks manuell purgen (VORSICHT!)
docker compose exec worker celery -A app.workers.celery_app.celery purge
```

---

### Problem: Hohe Memory-Nutzung

**Symptome:**
- Docker Desktop zeigt >80% Memory
- Container werden gekillt (OOMKilled)

**Diagnose:**
```bash
# Memory-Nutzung pro Container
docker stats --no-stream

# Top-Consumer finden
docker stats --no-stream | sort -k4 -h
```

**Lösung:**
```bash
# Kurzfristig: Ressourcen-Limits setzen
# In docker-compose.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

# Langfristig: DB-Connection-Pooling optimieren
# apps/api/app/db/session.py:
# pool_size=5, max_overflow=10
```

---

## 🔒 Security Checks

### Vor Deployment prüfen:
```bash
# 1. Keine Hardcoded Secrets
grep -r "password.*=" apps/api/ apps/web/ --include="*.py" --include="*.ts"

# 2. JWT_SECRET gesetzt und stark
docker compose exec backend env | grep JWT_SECRET
# Muss mindestens 32 Zeichen haben!

# 3. Security-Scan
docker compose run --rm backend semgrep --config auto apps/api/app

# 4. Dependency-Vulnerabilities
docker run --rm -v $(pwd):/app aquasec/trivy fs --severity HIGH,CRITICAL /app
```

### Security-Incident Response:
```bash
# 1. Sofort: Betroffene Services stoppen
docker compose stop backend

# 2. Logs sichern
docker compose logs backend > incident_$(date +%Y%m%d_%H%M%S).log

# 3. Rollback auf letzte sichere Version
git log --oneline -10
git checkout <safe-commit>
docker compose up -d --build

# 4. JWT-Secrets rotieren
# In .env: JWT_SECRET neu generieren
# Alle User müssen sich neu einloggen
```

---

## 📈 Performance-Monitoring

### Metriken sammeln
```bash
# Prometheus-Metriken abrufen
curl http://localhost:8000/metrics

# Wichtige Metriken:
# - http_requests_total (Request-Count)
# - http_request_duration_seconds (Latency)
# - process_resident_memory_bytes (Memory)
```

### Slow-Query-Log aktivieren
```bash
# PostgreSQL Slow-Query-Log
docker compose exec postgres psql -U coffeestudio -c "ALTER SYSTEM SET log_min_duration_statement = 1000;"
docker compose restart postgres

# Logs anzeigen
docker compose exec postgres tail -f /var/lib/postgresql/data/log/postgresql-*.log
```

### API-Latenz messen
```bash
# Einzelner Request
time curl http://localhost:8000/cooperatives

# Load-Test (mit Apache Bench)
ab -n 1000 -c 10 http://localhost:8000/health

# K6 Load-Test
k6 run scripts/load-test.js
```

---

## 🔄 Deployment

### Development → Staging
```bash
# 1. Alle Tests grün?
docker compose exec backend pytest

# 2. Security-Scan OK?
semgrep --config auto apps/api/app

# 3. Tag erstellen
git tag -a v0.3.0 -m "Phase 1 Security Fixes"
git push origin v0.3.0

# 4. Auf Staging deployen
# (Automatisch via GitHub Actions CD-Pipeline)
```

### Rollback-Strategie
```bash
# Docker Compose (Dev/Staging)
docker compose down
git checkout v0.2.1c  # Letzte stabile Version
docker compose up -d --build

# Kubernetes (Production)
kubectl rollout undo deployment/backend
kubectl rollout status deployment/backend -w

# Verify
curl http://localhost:8000/health
```

---

## 🚨 Alerts & SLOs

### Service Level Objectives (SLOs)
- **Uptime:** > 99.9% (max 43 Min Downtime/Monat)
- **Latency (p95):** < 500ms
- **Error Rate:** < 1%

### Alert-Regeln (Prometheus)
```yaml
# ops/prometheus-alerts.yml
groups:
  - name: coffeestudio
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Hohe Fehlerrate > 5%"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 0.5
        for: 10m
        annotations:
          summary: "p95-Latenz > 500ms"
      
      - alert: ServiceDown
        expr: up{job="apps/api"} == 0
        for: 1m
        annotations:
          summary: "Backend nicht erreichbar"
```

---

## 📞 Eskalation

### Severity-Level
- **P0 (Critical):** Service komplett down → Sofortiges Rollback
- **P1 (High):** Degraded Performance → Hotfix innerhalb 4h
- **P2 (Medium):** Feature-Bug → Fix im nächsten Sprint
- **P3 (Low):** Kosmetisch → Backlog

### On-Call Playbook
1. **Alert empfangen** → Check Grafana/Logs
2. **Impact bewerten** → Wie viele User betroffen?
3. **Mitigation** → Rollback oder Hotfix?
4. **Communication** → Status-Update an Stakeholder
5. **Post-Mortem** → Root-Cause-Analyse innerhalb 48h

---

## 📚 Weitere Docs
- [Deployment-Guide](./DEPLOYMENT_GUIDE.md)
- [Testing-Guide](./TESTING_GUIDE.md)
- [Architecture-Overview](./docs/ARCHITECTURE.md)

---

**Letzte Aktualisierung:** 2025-12-28  
**Verantwortlich:** DevOps-Team