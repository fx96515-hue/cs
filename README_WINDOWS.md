# CoffeeStudio (Option D) – Windows Quickstart (PowerShell)

## Voraussetzungen
- **Docker Desktop** (WSL2 / Linux containers)
- **Git**
- **Python 3.11+**
- **Node.js 20+** (für `apps/web`)

Optional (empfohlen):
- **ripgrep** (für schnelle Repo-Suche)
  - `winget install BurntSushi.ripgrep.MSVC`

## Wichtig: Docker Desktop / Linux Engine
Wenn du Fehler wie `dockerDesktopLinuxEngine ... pipe ... not found` siehst:
- Docker Desktop starten
- sicherstellen, dass **Linux containers / WSL2 Backend** aktiv ist
- prüfen:
  - `docker context ls`
  - `docker context show`
  - `docker version` (muss **Client + Server** anzeigen)

## Dev-Stack starten (empfohlen)
1) Repo-Root:
   - `.\run_windows.ps1`

Das Script:
- legt `.env` aus `.env.example` an (falls fehlt)
- startet `docker compose up`
- führt Migrationen aus
- bootstrapped Dev-Admin

## Enterprise-Stack starten
- `.\scripts\start_enterprise.ps1 -action start -FollowLogs`

Env:
- Vorlage: `infra/env/enterprise.env.example`
- Lokal: `infra/env/enterprise.env` (wird automatisch kopiert, falls fehlt)
  - **Wichtig:** `infra/env/enterprise.env` ist absichtlich in `.gitignore`.

## Quality Checks (Windows)
- `.\scripts\win\10_quality_check.ps1`
