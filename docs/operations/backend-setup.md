# Backend Setup Instructions

## ✅ Status: VOLLSTÄNDIG FUNKTIONSFÄHIG

Das Backend ist jetzt vollständig kompatibel und lauffähig!

## 🔧 Behobene Probleme

### 1. Alpine/Debian Inkompatibilität
- **Vorher:** Multi-stage Build mit Debian (builder) + Alpine (runtime)
- **Problem:** Pydantic Binary Wheels benötigen glibc (nicht musl libc)
- **Lösung:** Runtime Stage auf `python:3.12-slim` (Debian) umgestellt
- **Ergebnis:** ✅ Alle Python Packages laden korrekt

### 2. Fehlende ML Build Dependencies
- **Problem:** gcc, g++ fehlten für numpy/pandas/scikit-learn
- **Lösung:** Build-Tools im Builder Stage hinzugefügt
- **Ergebnis:** ✅ ML Packages kompilieren erfolgreich

### 3. Alembic Migration Chain
- **Problem:** Doppelte Migrationen mit falschen Revision-Referenzen
- **Lösung:** 
  - Entfernt: `0009_peru_sourcing_intelligence_v0_4_0.py`
  - Entfernt: `0010_peru_sourcing_intelligence_v0_4_0.py`
  - Fixed: `0010_seed_ml_data.py` (psycopg3 Kompatibilität)
- **Ergebnis:** ✅ Alle Migrationen laufen fehlerfrei

## 🚀 Schnellstart

### 1. .env Datei erstellen
```bash
cp .env.example .env
```

Dann `.env` editieren und mindestens diese Werte setzen:
```env
JWT_SECRET=dev_secret_change_me_minimum_32_characters_long_for_security
BOOTSTRAP_ADMIN_EMAIL=admin@coffeestudio.com
BOOTSTRAP_ADMIN_PASSWORD=admin_dev_password_change_in_production
DATABASE_URL=postgresql+psycopg://coffeestudio:coffeestudio@postgres:5432/coffeestudio
REDIS_URL=redis://redis:6379/0
```

### 2. Services starten
```bash
docker compose up -d
```

### 3. Status prüfen
```bash
docker compose ps
```

Alle Services sollten "healthy" sein:
- ✅ postgres
- ✅ redis
- ✅ backend
- ✅ worker
- ✅ beat

### 4. Health Check
```bash
curl http://localhost:8000/health
```

Erwartete Antwort:
```json
{"status": "ok"}
```

### 5. Logs prüfen (optional)
```bash
docker compose logs backend -f
```

## 📋 Migration Chain

Die korrekte Migrations-Kette ist jetzt:
1. 0001_init
2. 0002_market_reports_sources_lots
3. 0003_entity_evidence
4. 0004_roaster_contact_email
5. 0005_data_backbone_v0_3_0
6. 0006_kb_and_cupping_v0_3_0
7. 0007_market_observation_uniques_v0_3_1
8. 0008_timestamp_defaults_kb_cupping_v0_3_2b
9. 0009_ml_prediction_tables
10. 0010_seed_ml_data
11. 0011_add_shipments_table

## 🔍 Fehlerbehebung

### Backend startet nicht
1. Prüfen Sie, ob `.env` existiert und korrekte Werte hat
2. Prüfen Sie logs: `docker compose logs backend`
3. Rebuild: `docker compose build backend --no-cache`

### Migrations schlagen fehl
- Prüfen Sie, dass keine alten Duplikat-Migrationen existieren
- Bei Bedarf Database neu erstellen: `docker compose down -v && docker compose up -d`

### Permission Denied Fehler
- Docker neu starten
- Images neu bauen: `docker compose build --no-cache`

## 🎯 Wichtige Änderungen

### Dockerfile (apps/api/Dockerfile)
- ✅ Runtime: `python:3.12-slim` (vorher: `python:3.12-alpine`)
- ✅ Package Manager: `apt-get` (vorher: `apk`)
- ✅ Runtime Libs: `libpq5` (vorher: `libpq`)
- ✅ User Creation: `groupadd`/`useradd` (vorher: `addgroup`/`adduser`)
- ✅ Build Dependencies: gcc, g++, libpq-dev hinzugefügt

### Alembic Migrations
- ❌ Entfernt: `0009_peru_sourcing_intelligence_v0_4_0.py` (Duplikat)
- ❌ Entfernt: `0010_peru_sourcing_intelligence_v0_4_0.py` (Duplikat)
- ✅ Fixed: `0010_seed_ml_data.py` (psycopg3 Kompatibilität)

## ✅ Validation

Alle Tests bestanden:
- ✅ Docker Build erfolgreich
- ✅ Alle Packages installiert
- ✅ Pydantic Core lädt korrekt
- ✅ Alle Migrationen laufen durch
- ✅ Backend startet und ist healthy
- ✅ Health Endpoint antwortet
- ✅ Keine Security Vulnerabilities

**Status:** 🟢 PRODUCTION READY
