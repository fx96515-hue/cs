# CoffeeStudio – Lokal starten & mit GitHub arbeiten

> Dieser Leitfaden erklärt genau wie du das Projekt von v0 auf deinen lokalen VS Code
> bringst, das Backend anschliessst und mit GitHub zusammenarbeitest.

---

## 1. Projekt von GitHub nach VS Code holen

Das Projekt ist bereits mit GitHub verbunden (Repo: `fx96515-hue/cs`).

```bash
# Repository klonen
git clone https://github.com/fx96515-hue/cs.git coffeestudio
cd coffeestudio

# Aktuellen Branch von v0 holen (hier liegen alle v0-Änderungen)
git fetch origin
git checkout v0/fx96515-hue-57428183

# Oder: neuen lokalen Branch von diesem Stand ableiten
git checkout -b main origin/v0/fx96515-hue-57428183
```

---

## 2. Abhängigkeiten installieren

```bash
# pnpm ist der Package-Manager dieses Projekts
npm install -g pnpm

# Alle Frontend-Abhängigkeiten installieren
cd apps/web
pnpm install
```

---

## 3. Umgebungsvariablen setzen

Erstelle die Datei `apps/web/.env.local`:

```bash
# Zeigt auf dein lokales Backend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 4. Frontend starten

```bash
cd apps/web
pnpm dev
# → http://localhost:3000
```

Ohne Backend: Klick auf "Demo-Modus" auf der Login-Seite.
Mit Backend: Normale Anmeldung mit echten Zugangsdaten.

---

## 5. Backend starten (Python/FastAPI)

Das Backend liegt im Repo unter `apps/api/` (oder dem entsprechenden Verzeichnis).

```bash
cd apps/api

# Python-Umgebung (uv empfohlen)
pip install uv
uv sync

# Umgebungsvariablen
cp .env.example .env
# .env anpassen: DATABASE_URL, JWT_SECRET_KEY, etc.

# Server starten
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# → http://localhost:8000/docs (OpenAPI)
```

**Prüfen ob alles läuft:**
```bash
curl http://localhost:8000/health
# → {"status": "ok"}

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=deinpasswort"
# → {"ok": true, "user": {...}}
```

---

## 6. Was du im Backend implementieren musst

Die vollständige Spezifikation steht in `ENTERPRISE_ROADBOOK.md`.
Hier die Kurzfassung in der richtigen Reihenfolge:

### Woche 1 — Authentifizierung (höchste Priorität)

**Ziel:** Login funktioniert lokal ohne Demo-Modus.

1. `POST /auth/login` — gibt `{"ok": true, "user": {...}}` zurück
2. `POST /auth/logout` — löscht Session
3. CORS konfigurieren mit `allow_credentials=True`

Das Frontend sendet aktuell noch den Token an `localStorage`.
Der Route-Guard in `proxy.ts` ist schon fertig — er wird automatisch aktiv
sobald der Token als `httpOnly`-Cookie kommt (Schritt 1 im Roadbook).

### Woche 2 — Token Refresh

4. `POST /auth/refresh` — erneuert Token transparent
5. `GET /auth/me` — gibt eingeloggten User zurück

Das Frontend ruft bei jedem `401` automatisch `/auth/refresh` auf — die Logik
ist bereits in `lib/api.ts` implementiert.

### Woche 3 — Kernendpunkte

6. `GET/POST/PATCH/DELETE /roasters` mit Query-Parametern
7. `GET/POST/PATCH/DELETE /cooperatives` mit Query-Parametern
8. Beide geben `{"items": [...], "total": N, "page": 1, "limit": 25}` zurück

### Woche 4 — Restliche Endpunkte

9. `/lots`, `/shipments`, `/deals`, `/alerts`
10. `/ml`, `/sentiment`, `/news`, `/reports`
11. `/ops`, `/dedup`, `/graph`

Alle Endpunkte mit Query-Parametern sind in `ENTERPRISE_ROADBOOK.md`
Abschnitt "Schritt 7" vollständig dokumentiert.

---

## 7. GitHub-Workflow

### Branches verstehen

```
main (oder master)           ← Stabiler Stand
  └── v0/fx96515-hue-57428183  ← Alle v0-Änderungen (Frontend)
  └── feature/backend-auth      ← Deine Backend-Arbeit
  └── feature/api-roasters       ← Endpunkte schrittweise
```

### Empfohlener Workflow

```bash
# Neuen Feature-Branch für Backend-Arbeit erstellen
git checkout -b feature/backend-auth

# Arbeiten, committen
git add apps/api/
git commit -m "feat(auth): add login endpoint with httpOnly cookie"

# Zum Remote pushen
git push origin feature/backend-auth

# Pull Request auf GitHub erstellen
# → merge in main wenn getestet
```

### v0-Änderungen holen (wenn du in v0 weiterarbeitest)

```bash
# v0 pusht auf: v0/fx96515-hue-57428183
git fetch origin
git merge origin/v0/fx96515-hue-57428183

# Oder als rebase:
git rebase origin/v0/fx96515-hue-57428183
```

---

## 8. VS Code empfohlene Extensions

Installiere diese Extensions für optimale Entwicklungserfahrung:

```
ms-python.python              # Python
ms-python.vscode-pylance      # Python Intellisense
charliermarsh.ruff             # Python Linting
bradlc.vscode-tailwindcss     # Tailwind CSS Autocomplete
esbenp.prettier-vscode        # Code Formatting
dbaeumer.vscode-eslint        # ESLint
prisma.prisma                 # Falls du Prisma nutzt
ms-vscode.vscode-typescript-next  # TypeScript
```

**VS Code Workspace-Datei** (`coffeestudio.code-workspace`):

```json
{
  "folders": [
    { "name": "Frontend", "path": "apps/web" },
    { "name": "Backend", "path": "apps/api" },
    { "name": "Root", "path": "." }
  ],
  "settings": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "[python]": {
      "editor.defaultFormatter": "charliermarsh.ruff"
    },
    "typescript.tsdk": "apps/web/node_modules/typescript/lib"
  }
}
```

---

## 9. Mit OpenAI lokal arbeiten

Das Roadbook (`ENTERPRISE_ROADBOOK.md`) ist genau dafür vorbereitet.
So nutzt du es effektiv mit ChatGPT/lokalen Modellen:

### Prompt-Vorlage für Backend-Entwicklung

```
Ich entwickle das Backend für CoffeeStudio, eine Enterprise-Plattform
für Kaffeebeschaffung. Das Frontend ist fertig und in TypeScript/Next.js
implementiert.

Ich benötige jetzt den FastAPI-Endpunkt für: [ENDPUNKT]

Anforderungen aus dem Roadbook:
- Endpunkt: [z.B. GET /roasters]
- Response-Format: {"items": [...], "total": N, "page": 1, "limit": 25}
- Query-Parameter: search, country, roaster_type, archived, page, limit
- Fehlerformat: {"detail": "...", "code": "...", "fields": {...}}

Bestehende Projekt-Struktur:
- FastAPI mit AsyncSession (SQLAlchemy)
- PostgreSQL Datenbank
- JWT Auth mit httpOnly Cookie

Erstelle: Router, Schema (Pydantic), Service-Funktion, und SQLAlchemy-Query.
```

### Kontext-Dateien die du OpenAI geben solltest

1. `ENTERPRISE_ROADBOOK.md` — vollständige API-Spezifikation
2. `apps/web/app/types/index.ts` — alle TypeScript-Interfaces (zeigt Datenstruktur)
3. `apps/web/app/services/*.service.ts` — zeigt welche Methoden das Frontend aufruft
4. Dein bestehendes Backend-Modell (z.B. `apps/api/app/models/roaster.py`)

---

## 10. Täglicher Entwicklungsablauf

```bash
# Morgens: Neueste Änderungen holen
git pull origin main
git pull origin v0/fx96515-hue-57428183  # v0-Updates holen falls vorhanden

# Frontend starten (Terminal 1)
cd apps/web && pnpm dev

# Backend starten (Terminal 2)
cd apps/api && uv run uvicorn app.main:app --reload

# Browser öffnen
# http://localhost:3000  ← Frontend
# http://localhost:8000/docs  ← Backend API-Docs

# Abends: Committen und pushen
git add .
git commit -m "feat: beschreibung der änderung"
git push origin feature/mein-branch
```

---

## 11. Typische Probleme beim ersten Start

| Problem | Lösung |
|---|---|
| `pnpm: command not found` | `npm install -g pnpm` |
| `Module not found: lib/api` | `pnpm install` im `apps/web` Verzeichnis |
| Frontend zeigt Demo-Banner | Backend läuft nicht oder `.env.local` fehlt |
| `CORS error` im Browser | Backend: `allow_credentials=True`, Origin `http://localhost:3000` |
| `401 Unauthorized` überall | Cookie `Secure=false` für lokale HTTP-Entwicklung setzen |
| TypeScript-Fehler in `services/` | `pnpm tsc --noEmit` für detaillierte Fehlerliste |
| Git-Konflikt beim Merge | Frontend-Dateien bevorzugen v0-Stand, Backend-Dateien deinen Stand |

---

## Zusammenfassung: Reihenfolge

```
1. git clone → git checkout v0-Branch
2. pnpm install → .env.local erstellen → pnpm dev
3. Demo-Login testen (ohne Backend)
4. Backend: /auth/login implementieren (Roadbook Schritt 1)
5. Echten Login testen
6. Schrittweise weitere Endpunkte (Roadbook Schritt 7)
7. Nach jedem Endpunkt: im Frontend testen, committen, pushen
```
