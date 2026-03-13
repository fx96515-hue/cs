# CoffeeStudio – Enterprise Roadbook

**Version:** 1.0 | **Stand:** 2026-03 | **Ziel:** Production-Ready Enterprise-Stack

Dieses Dokument beschreibt exakt was im Frontend bereits vorbereitet ist, was das Backend liefern muss, und in welcher Reihenfolge Frontend und Backend zusammengebracht werden. Jeder Schritt ist unabhängig testbar.

---

## Inhaltsverzeichnis

1. [Aktueller Frontend-Stand](#1-aktueller-frontend-stand)
2. [Backend-Anforderungen pro Schritt](#2-backend-anforderungen)
3. [Schritt 1 – httpOnly-Cookie Auth](#schritt-1--httpcookie-auth)
4. [Schritt 2 – Token Refresh](#schritt-2--token-refresh)
5. [Schritt 3 – Strukturierte Fehler](#schritt-3--strukturierte-fehler)
6. [Schritt 4 – Route-Guard aktivieren](#schritt-4--route-guard-aktivieren)
7. [Schritt 5 – Service-Layer verbinden](#schritt-5--service-layer-verbinden)
8. [Schritt 6 – React Query Hooks scharf schalten](#schritt-6--react-query-hooks)
9. [Schritt 7 – Vollständige API-Verträge](#schritt-7--vollständige-api-verträge)
10. [Umgebungsvariablen Referenz](#umgebungsvariablen-referenz)
11. [Lokale Entwicklung Checkliste](#lokale-entwicklung-checkliste)

---

## 1. Aktueller Frontend-Stand

### Was bereits vorbereitet ist

| Komponente | Datei | Status |
|---|---|---|
| API-Client mit `ApiError`-Klasse | `lib/api.ts` | Bereit |
| 401 Auto-Refresh-Logik | `lib/api.ts` | Bereit, wartet auf Backend-Endpunkt |
| Service-Layer | `app/services/*.service.ts` | Bereit |
| React Query Hooks | `app/hooks/use*.ts` | Bereit, `staleTime: 5min` |
| Route-Guard Middleware | `middleware.ts` | Bereit, wartet auf httpOnly-Cookie |
| Toast-System | `app/components/ToastProvider.tsx` | Aktiv |
| Demo-Modus-Guard | `lib/api.ts → isDemoMode()` | Aktiv |
| Breadcrumbs | `app/components/Breadcrumb.tsx` | Aktiv |
| Command-Palette | `app/components/CommandPalette.tsx` | Aktiv |
| Pagination | `app/components/Pagination.tsx` | Aktiv |
| CSV-Export | `app/utils/export.ts` | Aktiv |
| Strukturierter Fehler-Handler | `app/utils/error.ts` | Aktiv |

### Was noch localStorage verwendet (temporär)

Der Token liegt aktuell in `localStorage`. Das ist für die Preview-Umgebung funktional, aber nicht produktionstauglich. Die Umstellung auf `httpOnly`-Cookie ist in Schritt 1 beschrieben. Das Frontend ist bereits vollständig darauf vorbereitet.

---

## 2. Backend-Anforderungen

### Schnellübersicht – Was das Backend braucht

| Schritt | Backend-Änderung | Priorität |
|---|---|---|
| 1 | `POST /auth/login` → setzt `httpOnly`-Cookie | Kritisch |
| 1 | `POST /auth/logout` → löscht Cookie | Kritisch |
| 2 | `POST /auth/refresh` → erneuert Token | Hoch |
| 3 | Einheitliches Fehlerformat `{detail, code}` | Hoch |
| 5 | Paginierte Antworten für alle Listenendpunkte | Mittel |
| 7 | OpenAPI-Schema vollständig und aktuell | Mittel |

---

## Schritt 1 – httpOnly-Cookie Auth

### Problem heute
`localStorage.setItem("token", ...)` ist per JavaScript lesbar. XSS-Angriff = Token gestohlen.

### Lösung

**Backend: FastAPI**

```python
# app/routers/auth.py
from fastapi import APIRouter, Response, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "token"
COOKIE_MAX_AGE = 60 * 60 * 8  # 8 Stunden

@router.post("/login")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Ungültige Zugangsdaten")
    
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    
    # httpOnly-Cookie setzen — nicht per JS lesbar
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=True,          # nur HTTPS — in dev: False
        samesite="strict",
        max_age=COOKIE_MAX_AGE,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=60 * 60 * 24 * 7,  # 7 Tage
        path="/auth/refresh",       # nur für Refresh-Endpunkt sichtbar
    )
    
    # Kein Token im Body — nur als Cookie
    return {"ok": True, "user": {"email": user.email, "role": user.role}}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    response.delete_cookie("refresh_token", path="/auth/refresh")
    return {"ok": True}
```

**CORS-Konfiguration (wichtig für Cookies)**

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://ui.localhost"],
    allow_credentials=True,   # MUSS true sein für Cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Frontend: Next.js API-Route** (Bridge zwischen Browser und Backend)

Datei: `apps/web/app/api/auth/login/route.ts`

```typescript
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.json();
  
  // Backend aufrufen
  const backendRes = await fetch(`${process.env.API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      username: body.email,
      password: body.password,
    }),
    credentials: "include",
  });
  
  if (!backendRes.ok) {
    const err = await backendRes.json().catch(() => ({}));
    return NextResponse.json(
      { detail: err.detail || "Anmeldung fehlgeschlagen" },
      { status: backendRes.status }
    );
  }
  
  const data = await backendRes.json();
  
  // Cookie vom Backend an den Browser weiterleiten
  const res = NextResponse.json(data);
  const setCookie = backendRes.headers.get("set-cookie");
  if (setCookie) res.headers.set("set-cookie", setCookie);
  
  return res;
}
```

Datei: `apps/web/app/api/auth/logout/route.ts`

```typescript
import { NextResponse } from "next/server";
import { cookies } from "next/headers";

export async function POST() {
  const res = NextResponse.json({ ok: true });
  res.cookies.delete("token");
  res.cookies.delete("refresh_token");
  return res;
}
```

**Login-Seite aktualisieren** (`app/login/page.tsx`):

Statt `setToken(data.access_token)` → API-Route aufrufen:

```typescript
// In der handleSubmit-Funktion:
const res = await fetch("/api/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password }),
  credentials: "include",
});

if (!res.ok) {
  const err = await res.json();
  setError(err.detail || "Anmeldung fehlgeschlagen");
  return;
}

// Kein Token in localStorage mehr — Cookie wird automatisch gesetzt
router.push("/dashboard");
```

**`lib/api.ts` Anpassung** (Fetch mit Cookie):

```typescript
// In apiFetch, die tryFetch-Funktion:
const res = await fetch(u, {
  ...req,
  headers,
  credentials: "include",  // Cookie mitsenden
});
```

---

## Schritt 2 – Token Refresh

Das Frontend ruft bei jedem 401 automatisch `POST /auth/refresh` auf (bereits implementiert in `lib/api.ts`).

**Backend**:

```python
@router.post("/refresh")
async def refresh(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Kein Refresh-Token")
    
    try:
        payload = decode_token(refresh_token)
        user = await get_user_by_email(db, payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Ungültiger Refresh-Token")
    
    new_access_token = create_access_token({"sub": user.email})
    
    response.set_cookie(
        key="token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=60 * 60 * 8,
    )
    
    # Frontend erwartet dieses Format:
    return {"access_token": new_access_token, "token_type": "bearer"}
```

**Frontend-Verhalten** (bereits in `lib/api.ts` implementiert):
1. Request schlägt mit 401 fehl
2. `apiFetch` ruft `POST /auth/refresh` auf
3. Erhält neuen Token, setzt ihn
4. Wiederholt den ursprünglichen Request transparent
5. Wenn Refresh auch 401 → `setToken(null)` → User landet auf `/login`

---

## Schritt 3 – Strukturierte Fehler

Das Frontend erwartet dieses JSON-Format bei Fehlern (implementiert in `ApiError`-Klasse):

```json
{
  "detail": "Menschenlesbarer Fehlertext auf Deutsch",
  "code": "VALIDATION_ERROR",
  "fields": {
    "price_per_kg": "Muss größer als 0 sein"
  }
}
```

**Backend FastAPI Exception Handler:**

```python
# app/main.py
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    fields = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        fields[field] = error["msg"]
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validierungsfehler – bitte Eingaben prüfen",
            "code": "VALIDATION_ERROR",
            "fields": fields,
        },
    )

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Ressource nicht gefunden",
            "code": "NOT_FOUND",
        },
    )
```

**Frontend-Nutzung** (`app/utils/error.ts` erkennt `ApiError` bereits):

```typescript
// In Formular-Komponenten:
import { ApiError } from "../../lib/api";

try {
  await RoastersService.create(data);
} catch (e) {
  if (e instanceof ApiError && e.isValidation) {
    // Feldspezifische Fehler anzeigen
    const fields = (e.detail as any)?.fields ?? {};
    setFieldErrors(fields);
  } else {
    toast.error(toErrorMessage(e));
  }
}
```

---

## Schritt 4 – Route-Guard aktivieren

Die `middleware.ts` ist bereits vorhanden und schützt alle Routen. Sie greift sobald der Token als Cookie kommt (Schritt 1). **Keine weiteren Änderungen nötig.**

Solange noch `localStorage` verwendet wird, bleibt der Guard passiv — `AppShell` übernimmt den Client-seitigen Schutz.

**Aktivierungsprüfung:**

```bash
# Cookie setzen (nach Schritt 1)
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"test"}'

# Prüfen ob Cookie gesetzt wurde
# → Set-Cookie: token=eyJ...; Path=/; HttpOnly; SameSite=Strict

# Geschützte Route ohne Cookie aufrufen
curl http://localhost:3000/roasters
# → 307 Redirect zu /login?next=/roasters
```

---

## Schritt 5 – Service-Layer verbinden

Der Service-Layer (`app/services/*.service.ts`) ist vollständig implementiert. Alle Methoden rufen `apiFetch` auf. **Keine Backend-Änderungen nötig** — vorausgesetzt die API-Endpunkte entsprechen den Verträgen in Schritt 7.

**Verwendungsbeispiel in einer Komponente:**

```typescript
// Alt (direkt in page.tsx):
const data = await apiFetch<Roaster[]>("/roasters");

// Neu (über Service):
import { RoastersService } from "../services";
const data = await RoastersService.list({ country: "DE", page: 1 });
```

**Vorhandene Services:**

| Service | Datei | Methoden |
|---|---|---|
| Auth | `services/auth.service.ts` | `login`, `logout`, `me`, `refresh` |
| Röstereien | `services/roasters.service.ts` | `list`, `getById`, `create`, `update`, `archive`, `restore` |
| Kooperativen | `services/cooperatives.service.ts` | `list`, `getById`, `create`, `update`, `archive`, `enrich` |
| Lots/Partien | `services/lots.service.ts` | `list`, `getById`, `create`, `update`, `calcMargin`, `getMarginHistory` |
| Sendungen | `services/shipments.service.ts` | `list`, `getById`, `create`, `update`, `addEvent` |
| Deals | `services/deals.service.ts` | `list`, `getById`, `create`, `update`, `close` |
| Alerts | `services/alerts.service.ts` | `list`, `getStats`, `resolve`, `resolveAll` |

---

## Schritt 6 – React Query Hooks

Alle Hooks in `app/hooks/` verwenden React Query mit `staleTime: 5 * 60 * 1000`. Sie sind bereits mit `isDemoMode()`-Guard versehen.

**Scharf-Schalten:**

Die Hooks ersetzen schrittweise die manuellen `useEffect + fetch`-Pattern. Vorgehen pro Seite:

```typescript
// Alt (in page.tsx):
const [roasters, setRoasters] = useState([]);
useEffect(() => {
  apiFetch("/roasters").then(setRoasters);
}, []);

// Neu (über Hook):
import { useRoasters } from "../hooks/useRoasters";
const { data, isLoading, error, refetch } = useRoasters({ country: "DE" });
const roasters = data?.items ?? [];
```

**Query-Keys Übersicht** (`app/hooks/query-keys.ts`):

```
roasters.all         → ["roasters", "list"]
roasters.byId(1)     → ["roasters", "detail", 1]
cooperatives.all     → ["cooperatives", "list"]
cooperatives.byId(1) → ["cooperatives", "detail", 1]
shipments.all        → ["shipments", "list"]
deals.all            → ["deals", "list"]
alerts.all           → ["alerts"]
```

**Cache-Invalidierung nach Mutation:**

```typescript
const queryClient = useQueryClient();

// Nach Archivieren einer Rösterei:
queryClient.invalidateQueries({ queryKey: ["roasters"] });

// Nach Update einer Kooperative:
queryClient.invalidateQueries({ queryKey: ["cooperatives", "detail", id] });
```

---

## Schritt 7 – Vollständige API-Verträge

### Alle erwarteten Endpunkte

#### Auth
```
POST   /auth/login              → {ok: true, user: {email, role}}
POST   /auth/logout             → {ok: true}
POST   /auth/refresh            → {access_token, token_type}
GET    /auth/me                 → {id, email, role, created_at}
```

#### Röstereien
```
GET    /roasters                → Roaster[] | Paged<Roaster>
POST   /roasters                → Roaster
GET    /roasters/{id}           → Roaster
PATCH  /roasters/{id}           → Roaster
DELETE /roasters/{id}           → 204
POST   /roasters/{id}/restore   → Roaster
```

**Query-Parameter für GET /roasters:**
```
search, country, roaster_type, contact_status, archived
min_capacity, max_capacity, min_sales_fit_score
page, page_size (oder limit, offset)
```

#### Kooperativen
```
GET    /cooperatives             → Cooperative[] | Paged<Cooperative>
POST   /cooperatives             → Cooperative
GET    /cooperatives/{id}        → Cooperative
PATCH  /cooperatives/{id}        → Cooperative
DELETE /cooperatives/{id}        → 204
POST   /cooperatives/{id}/restore → Cooperative
POST   /cooperatives/{id}/enrich  → Cooperative
```

#### Lots/Kaffee-Partien
```
GET    /lots                     → Lot[] | Paged<Lot>
POST   /lots                     → Lot
GET    /lots/{id}                → Lot
PATCH  /lots/{id}                → Lot
DELETE /lots/{id}                → 204
POST   /lots/{id}/calc-margin    → MarginCalcResult
GET    /lots/{id}/margin-history → MarginRun[]
```

#### Sendungen
```
GET    /shipments                → Shipment[] | Paged<Shipment>
POST   /shipments                → Shipment
GET    /shipments/{id}           → Shipment
PATCH  /shipments/{id}           → Shipment
POST   /shipments/{id}/events    → ShipmentEvent
```

#### Deals
```
GET    /deals                    → Deal[] | Paged<Deal>
POST   /deals                    → Deal
GET    /deals/{id}               → Deal
PATCH  /deals/{id}               → Deal
DELETE /deals/{id}               → 204
POST   /deals/{id}/close         → Deal
```

#### Alerts / Data Quality
```
GET    /alerts                   → DataQualityFlag[]
GET    /alerts/stats             → {critical, warning, total}
POST   /alerts/{id}/resolve      → DataQualityFlag
POST   /alerts/resolve-all       → {resolved: number}
```

#### ML / Vorhersagen
```
POST   /ml/predict/freight       → FreightPredictionResponse
POST   /ml/predict/price         → PricePredictionResponse
GET    /ml/models                → MLModel[]
POST   /ml/models/{type}/train   → {status, started_at}
```

#### Sentiment / News
```
GET    /sentiment/{region}       → {data: SentimentEntry[], region: string}
GET    /news                     → NewsItem[]
```

#### Reports
```
GET    /reports                  → Report[]
POST   /reports/generate         → Report
GET    /reports/{id}             → Report
```

#### Betrieb
```
GET    /ops/stats                → OpsStats
GET    /ops/logs                 → OpsLogEntry[]
GET    /ops/quality              → QualityStats
```

#### Deduplizierung
```
GET    /dedup/pairs/{entity_type} → DuplicatePair[]
POST   /dedup/merge              → {merged_id: number}
```

#### Wissensgraph
```
GET    /graph/entities           → GraphEntity[]
GET    /graph/relationships      → GraphRelationship[]
GET    /graph/entity/{id}        → GraphEntityDetail
```

### Paginiertes Antwortformat (Standard)

Das Frontend versteht beide Formate — bevorzugt wird das paginierte:

```json
{
  "items": [...],
  "total": 142,
  "page": 1,
  "limit": 25
}
```

Auch ein flaches Array `[...]` wird akzeptiert (Fallback in den Hooks).

---

## Umgebungsvariablen Referenz

### Frontend (`apps/web/.env.local`)

```bash
# API-URL die der Browser aufruft
NEXT_PUBLIC_API_URL=http://localhost:8000

# Für lokale Entwicklung mit Traefik:
# NEXT_PUBLIC_API_URL=http://api.localhost
```

### Backend (`.env`)

```bash
# Datenbank
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/coffeestudio

# JWT
JWT_SECRET_KEY=supersecretkey-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480    # 8 Stunden
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:3000,http://ui.localhost

# Cookie (prod: true, dev: false)
COOKIE_SECURE=false
```

---

## Lokale Entwicklung Checkliste

### 1. Backend starten

```bash
cd apps/api
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Prüfen:
- [ ] `http://localhost:8000/docs` öffnet OpenAPI-Dokumentation
- [ ] `POST /auth/login` gibt 200 zurück (nicht 404)
- [ ] Response enthält `Set-Cookie: token=...`

### 2. Frontend starten

```bash
cd apps/web
pnpm dev
```

Prüfen:
- [ ] `http://localhost:3000/login` öffnet Login-Seite
- [ ] Login mit echten Zugangsdaten → Redirect auf `/dashboard`
- [ ] Kein Demo-Mode-Banner sichtbar
- [ ] Browser DevTools → Application → Cookies → `token` ist gesetzt

### 3. API-Verbindung prüfen

```bash
# Manuell testen:
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=testpassword"
```

Erwartete Antwort:
```json
{"ok": true, "user": {"email": "admin@example.com", "role": "admin"}}
```

### 4. Schritt-für-Schritt Integration

```
Woche 1:  Schritt 1 (Login/Logout Cookie) + Schritt 3 (Fehlerformat)
Woche 2:  Schritt 2 (Token Refresh) + Schritt 4 (Route-Guard)
Woche 3:  Schritt 5 (Service-Layer) + Schritt 6 (React Query)
Woche 4:  Schritt 7 (alle Endpunkte vollständig) + E2E-Tests
```

### 5. Typische Fehler

| Fehler | Ursache | Lösung |
|---|---|---|
| `CORS error` | Backend CORS nicht konfiguriert | `allow_credentials=True` + korrekte Origins |
| `Cookie nicht gesetzt` | `credentials: "include"` fehlt im fetch | In `apiFetch` `credentials: "include"` hinzufügen |
| `401 bei jedem Request` | Cookie `Secure`-Flag in HTTP-Dev | `COOKIE_SECURE=false` im Backend |
| `Refresh-Loop` | `_isRetry`-Flag fehlt | Bereits korrekt in `lib/api.ts` implementiert |
| `Demo-Banner trotz echtem Login` | Token-Wert = `demo_token_for_preview` | Backend gibt anderen Token zurück |
| `Paginierung falsch` | Backend gibt Array statt `{items, total}` | Frontend-Fallback greift, aber `total` fehlt |

---

## Zusammenfassung

Das Frontend ist vollständig enterprise-ready vorbereitet:

- **Sicherheit:** `ApiError`-Klasse, 401-Auto-Refresh, `middleware.ts` Route-Guard (wartet auf Cookie)
- **Architektur:** Service-Layer (`services/*.ts`), React Query Hooks mit staleTime, zentrales Type-System (`types/index.ts`)
- **UX:** Toast-System, Command-Palette, Breadcrumbs, Pagination, CSV-Export, Offline-Indikator, Skeleton-Loading, Empty States, Collapsible Sidebar
- **Demo-Modus:** Alle Hooks und direkten `apiFetch`-Aufrufe haben `isDemoMode()`-Guard

---

## Schritt 8: KI-Analyst + Semantische Suche

Diese beiden Seiten sind vollständig neu aufgebaut und benötigen folgende Backend-Endpunkte.

### 8a. KI-Analyst (`/analyst`)

**Frontend-Datei:** `apps/web/app/analyst/page.tsx`

Der Analyst sendet eine Frage und erhält eine Antwort mit Quellen-Referenzen.

```python
# FastAPI — KI-Analyst Endpunkte

from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends
from .auth import get_current_user

router = APIRouter(prefix="/analyst", tags=["analyst"])

class AnalystQuestion(BaseModel):
    question: str                   # Freitext, max 1000 Zeichen
    conversation_history: list[dict] = []  # [{"role": "user"|"assistant", "content": "..."}]

class AnalystSource(BaseModel):
    entity_type: str                # "cooperative" | "roaster" | "lot"
    entity_id: int
    name: str
    similarity_score: float         # 0.0 – 1.0

class AnalystResponse(BaseModel):
    answer: str                     # Antwort-Text (Markdown erlaubt)
    sources: list[AnalystSource]    # Quellen aus der Vektordatenbank
    tokens_used: Optional[int] = None

class ServiceStatus(BaseModel):
    available: bool
    provider: str                   # "openai" | "anthropic" | "local"
    model: str                      # z.B. "gpt-4o"
    embedding_provider: str
    embedding_model: str            # z.B. "text-embedding-3-small"

@router.post("/ask", response_model=AnalystResponse)
async def ask_analyst(
    body: AnalystQuestion,
    current_user=Depends(get_current_user),
):
    """
    Führt eine RAG-Anfrage durch:
    1. Frage in Embeddings umwandeln
    2. Ähnliche Entitäten aus der Vektordatenbank suchen
    3. Kontext + Frage an LLM senden
    4. Antwort + Quellen zurückgeben
    """
    # Implementierung: OpenAI Embeddings + pgvector oder Pinecone
    # Beispiel-Antwort:
    return AnalystResponse(
        answer="Basierend auf den Daten in der Datenbank...",
        sources=[
            AnalystSource(
                entity_type="cooperative",
                entity_id=42,
                name="Cooperativa Junín",
                similarity_score=0.92,
            )
        ],
        tokens_used=412,
    )

@router.get("/status", response_model=ServiceStatus)
async def get_analyst_status(current_user=Depends(get_current_user)):
    """Gibt zurück ob der KI-Service verfügbar ist und welches Modell verwendet wird."""
    return ServiceStatus(
        available=True,
        provider="openai",
        model="gpt-4o",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
    )
```

**Empfohlene Umgebungsvariablen im Backend:**

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
VECTOR_DB_URL=postgresql://...   # pgvector oder eigene Vektordatenbank
```

**Empfohlene Prompting-Strategie:**

```python
SYSTEM_PROMPT = """
Du bist ein spezialisierter Analyst für die CoffeeStudio B2B-Plattform.
Du hast Zugriff auf Daten zu Kooperativen, Röstereien, Kaffee-Partien und Lieferketten in Peru.
Antworte auf Deutsch, präzise und faktenbasiert.
Zitiere immer die Quellen wenn du auf konkrete Datenbankeinträge verweist.
Wenn du etwas nicht weißt, sage es klar — erfinde keine Daten.
"""
```

---

### 8b. Semantische Suche (`/search`)

**Frontend-Datei:** `apps/web/app/search/page.tsx`

```python
# FastAPI — Semantische Suche Endpunkte

class SearchRequest(BaseModel):
    query: str                      # Suchbegriff (Freitext oder strukturiert)
    entity_type: str = "cooperative" # "cooperative" | "roaster" | "lot"
    limit: int = 20
    min_score: float = 0.0

class SearchResult(BaseModel):
    entity_type: str
    entity_id: int
    name: str
    similarity_score: float         # 0.0 – 1.0, semantische Ähnlichkeit
    region: Optional[str] = None
    city: Optional[str] = None
    certifications: Optional[str] = None
    total_score: Optional[float] = None  # Qualitätsbewertung 0-100

class SearchResponse(BaseModel):
    query: str
    entity_type: str
    results: list[SearchResult]
    total: int

class SimilarEntity(BaseModel):
    entity_type: str
    entity_id: int
    name: str
    similarity_score: float

@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    body: SearchRequest,
    current_user=Depends(get_current_user),
):
    """
    Semantische Vektordatenbank-Suche.
    Konvertiert Query zu Embeddings, sucht ähnliche Einträge via pgvector.
    """
    pass

@router.get(
    "/search/similar/{entity_type}/{entity_id}",
    response_model=list[SimilarEntity],
)
async def find_similar(
    entity_type: str,
    entity_id: int,
    limit: int = 5,
    current_user=Depends(get_current_user),
):
    """Findet ähnliche Entitäten zu einem gegebenen Eintrag (z.B. ähnliche Kooperativen)."""
    pass
```

**Vektordatenbank-Setup mit pgvector:**

```sql
-- PostgreSQL Extension aktivieren
CREATE EXTENSION IF NOT EXISTS vector;

-- Embeddings-Tabelle
CREATE TABLE entity_embeddings (
    id          SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,   -- 'cooperative', 'roaster', 'lot'
    entity_id   INTEGER NOT NULL,
    content     TEXT NOT NULL,          -- Volltext der Entität (für Embedding)
    embedding   vector(1536),           -- OpenAI text-embedding-3-small = 1536 dim
    updated_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity_type, entity_id)
);

-- Index für schnelle Vektorsuche
CREATE INDEX ON entity_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Embeddings befüllen (Background-Job):**

```python
async def embed_entity(entity_type: str, entity_id: int, content: str):
    """
    Generiert Embedding für eine Entität und speichert es in der DB.
    Sollte nach jedem CREATE/UPDATE einer Entität aufgerufen werden.
    """
    import openai
    response = await openai.embeddings.create(
        model="text-embedding-3-small",
        input=content,
    )
    embedding = response.data[0].embedding
    # In DB speichern via pgvector
    await db.execute(
        """
        INSERT INTO entity_embeddings (entity_type, entity_id, content, embedding)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (entity_type, entity_id)
        DO UPDATE SET content=$3, embedding=$4, updated_at=NOW()
        """,
        entity_type, entity_id, content, embedding,
    )

# Content-Template pro Entität:
def cooperative_content(coop) -> str:
    return (
        f"Kooperative: {coop.name}. "
        f"Region: {coop.region}, {coop.country}. "
        f"Zertifizierungen: {coop.certifications}. "
        f"Qualitätsbewertung: {coop.total_score}. "
        f"Beschreibung: {coop.description or ''}. "
        f"Mitglieder: {coop.member_count or 'unbekannt'}."
    )
```

---

**Das Backend muss liefern:**
1. `POST /auth/login` mit `httpOnly`-Cookie
2. `POST /auth/refresh` Endpunkt
3. Einheitliches Fehlerformat `{detail, code}`
4. Alle Endpunkte aus Schritt 7 mit den beschriebenen Query-Parametern
5. `POST /analyst/ask` + `GET /analyst/status` (Schritt 8a)
6. `POST /search` + `GET /search/similar/{type}/{id}` (Schritt 8b)


