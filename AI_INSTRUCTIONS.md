# CoffeeStudio - Anweisungen fuer KI-Assistenten

## Kurzanleitung (Copy-Paste in ChatGPT/Copilot)

Wenn du mit diesem Projekt arbeitest, beachte folgende Regeln:

---

## 1. LIES ZUERST

Bevor du Code aenderst, lies immer:
- `CODEBASE_MAP.md` - Vollstaendige Projekt-Referenz
- `ENTERPRISE_ROADBOOK.md` - Backend-Spezifikation

---

## 2. PROJEKT-STRUKTUR

```
apps/
├── api/           # FastAPI Backend (Python)
│   ├── app/
│   │   ├── models/     # SQLAlchemy ORM
│   │   ├── routes/     # API Endpoints
│   │   ├── services/   # Business Logic
│   │   └── providers/  # Externe APIs
│   └── alembic/        # DB Migrationen
│
└── web/           # Next.js Frontend (TypeScript)
    ├── app/
    │   ├── components/ # React Components
    │   ├── services/   # API Service Layer
    │   ├── hooks/      # React Query Hooks
    │   └── types/      # TypeScript Interfaces
    └── lib/            # Utilities (api.ts)
```

---

## 3. REGELN (IMMER BEFOLGEN)

### Backend (Python)
- Alle DB-Operationen sind `async/await`
- Type Hints sind Pflicht
- Pydantic fuer alle Request/Response Schemas
- Provider-Module fuer externe APIs
- Service-Layer zwischen Routes und Providers

### Frontend (TypeScript)
- Typen aus `app/types/index.ts` importieren
- API-Calls ueber Services (`app/services/`)
- React Query fuer Data Fetching (`app/hooks/`)
- `isDemoMode()` Guard bei jedem API-Call
- CSS-Klassen aus `globals.css` (kein Tailwind)

---

## 4. CODE-BEISPIELE

### Neuer API-Endpoint (Backend)
```python
# 1. apps/api/app/routes/example_routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.example import ExampleRequest, ExampleResponse

router = APIRouter(prefix="/api/v1/example", tags=["Example"])

@router.post("/action", response_model=ExampleResponse)
async def do_action(
    request: ExampleRequest,
    db: AsyncSession = Depends(get_db)
):
    # Business logic hier
    return {"result": "success"}
```

### Neuer Service-Call (Frontend)
```typescript
// 1. apps/web/app/services/example.service.ts
import { apiFetch, isDemoMode } from "../../lib/api";
import { ExampleType } from "../types";

export const exampleService = {
  async list(): Promise<ExampleType[]> {
    if (isDemoMode()) return [];
    return apiFetch<ExampleType[]>("/api/v1/example");
  }
};

// 2. apps/web/app/hooks/useExample.ts
import { useQuery } from "@tanstack/react-query";
import { exampleService } from "../services/example.service";
import { queryKeys } from "./query-keys";
import { isDemoMode } from "../../lib/api";

export function useExample() {
  return useQuery({
    queryKey: queryKeys.example.list(),
    queryFn: () => exampleService.list(),
    enabled: !isDemoMode(),
  });
}
```

---

## 5. TESTING

```bash
# Backend Tests
cd apps/api
pytest tests/ -v

# Frontend Build Check
cd apps/web
pnpm build
```

---

## 6. HAEUFIGE FEHLER VERMEIDEN

| Fehler | Loesung |
|--------|---------|
| Typen inline definieren | Aus `types/index.ts` importieren |
| `apiFetch` direkt in Komponenten | Service oder Hook verwenden |
| Kein `isDemoMode()` Guard | Immer pruefen vor API-Call |
| CSS Inline-Styles | Klassen in `globals.css` definieren |
| Provider direkt in Route | Service-Layer dazwischen |

---

## 7. WICHTIGE DATEIEN

| Datei | Zweck |
|-------|-------|
| `lib/api.ts` | HTTP Client, Auth, Demo-Mode |
| `app/types/index.ts` | Alle TypeScript Interfaces |
| `app/services/index.ts` | Alle API Services |
| `globals.css` | Alle CSS Klassen |
| `core/config.py` | Backend Konfiguration |
| `db/session.py` | Database Session |

---

## 8. DATENBANK

13 Tabellen sind definiert. Wichtigste:

- `cooperatives` - Peru Kooperativen
- `roasters` - Deutsche Roestereien
- `lots` - Kaffee-Partien
- `deals` - Handelsgeschaefte
- `freight_history` - ML Training Daten
- `market_observations` - Echtzeit Marktdaten

---

## 9. EXTERNAL APIs (17 Quellen)

Alle ueber Provider-Module in `apps/api/app/providers/`:

| Provider | APIs |
|----------|------|
| `coffee_prices.py` | Yahoo Finance |
| `fx_rates.py` | ECB, OANDA |
| `weather.py` | OpenMeteo, RAIN4PE, NASA, SENAMHI |
| `shipping_data.py` | AIS, MarineTraffic |
| `news_market.py` | NewsAPI, Reddit, Twitter |
| `peru_macro.py` | INEI, BCRP, World Bank |

---

## 10. BEI FRAGEN

Wenn du unsicher bist:
1. Pruefe `CODEBASE_MAP.md` fuer Details
2. Suche nach aehnlichen Implementierungen im Code
3. Frage nach bevor du grosse Aenderungen machst

---

*Erstellt: Maerz 2026*
*Projekt: CoffeeStudio v2.0*
