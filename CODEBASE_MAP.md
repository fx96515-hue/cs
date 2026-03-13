
# CoffeeStudio — Codebase Map

Dieses Dokument ist der primäre Einstiegspunkt für KI-Assistenten (OpenAI, Copilot, etc.).
Lies es bevor du irgendetwas änderst. Es beschreibt wo was liegt und wie alles zusammenhängt.

---

## Repository-Struktur

```
cs/
├── apps/
│   └── web/                        ← Next.js 16 Frontend (einzige App)
│       ├── app/                    ← App Router (alle Seiten + Komponenten)
│       ├── lib/                    ← Shared Utilities (api.ts, queryClient.ts)
│       └── middleware.ts           ← Route-Guard (Auth-Schutz aller Seiten)
├── ENTERPRISE_ROADBOOK.md          ← Backend-Spezifikation (FastAPI-Endpunkte, Auth, Fehlerformat)
├── LOKAL_STARTEN.md                ← Lokales Setup, Git-Workflow, VS Code Einrichtung
└── CODEBASE_MAP.md                 ← Dieses Dokument
```

---

## Frontend: Wo was liegt

### Einstiegspunkte

| Datei | Zweck |
|---|---|
| `apps/web/lib/api.ts` | Zentraler HTTP-Client. Alle Requests laufen durch `apiFetch<T>()`. Enthält `ApiError`-Klasse, 401-Auto-Refresh, `isDemoMode()`. **Hier beginnt jede API-Änderung.** |
| `apps/web/middleware.ts` | Next.js Route-Guard. Schützt alle Routen außer `/login`. Liest Token aus Cookie (httpOnly) oder localStorage. |
| `apps/web/app/layout.tsx` | Root-Layout. Bindet `QueryClientProvider`, `AppShell`, Fonts ein. |
| `apps/web/app/globals.css` | Alle CSS-Custom-Properties (Design-Tokens). Kein Tailwind — reines CSS-Modul-System. |

### Typen

```
apps/web/app/types/index.ts         ← EINZIGE Quelle für alle TypeScript-Interfaces
                                      (Roaster, Cooperative, Lot, Shipment, Deal, Alert, ...)
                                      Niemals Typen in page.tsx inline definieren.
```

### Services (API-Aufrufe)

```
apps/web/app/services/
├── index.ts                        ← Re-exportiert alles, immer von hier importieren
├── auth.service.ts                 ← login(), logout(), refresh(), getCurrentUser()
├── roasters.service.ts             ← list(), getById(), create(), update(), archive(), restore()
├── cooperatives.service.ts         ← list(), getById(), create(), update(), enrich()
├── lots.service.ts                 ← list(), getById(), create(), update(), margin()
├── shipments.service.ts            ← list(), getById(), create(), update()
├── deals.service.ts                ← list(), getById(), create(), update(), close()
└── alerts.service.ts               ← list(), acknowledge(), resolve()
```

**Regel:** Komponenten rufen NIEMALS `apiFetch` direkt auf. Immer über Service oder Hook.

### React Query Hooks

```
apps/web/app/hooks/
├── query-keys.ts                   ← Zentrale Query-Key-Factory (queryKeys.roasters.list(f))
├── useRoasters.ts                  ← useRoasters(filters), useRoaster(id), Mutations
├── usePeruRegions.ts               ← useCooperatives(filters), useCooperative(id), Mutations
├── useShipments.ts                 ← useShipments(filters), useShipment(id)
├── useDeals.ts                     ← useDeals(filters), useDeal(id), Mutations
├── usePredictions.ts               ← usePricePrediction(), useFreightPrediction()
└── useLots.ts                      ← useLots(filters), useLot(id)
```

**Regel:** Alle Hooks prüfen `isDemoMode()` vor dem API-Aufruf und geben leere Defaults zurück.
**Caching:** `staleTime: 5 * 60 * 1000` (5 Minuten) auf allen List-Queries.

### Seiten

```
apps/web/app/
├── dashboard/page.tsx              ← KPI-Übersicht, Aktivitäten
├── roasters/
│   ├── page.tsx                    ← Liste mit Filter, Pagination, CSV-Export
│   └── [id]/page.tsx               ← Detail, Bearbeiten, Archivieren
├── cooperatives/
│   ├── page.tsx                    ← Liste mit Filter, Pagination, CSV-Export
│   └── [id]/page.tsx               ← Detail, Enrichment, Website-Analyse
├── lots/
│   ├── page.tsx                    ← Kaffee-Partien Liste
│   └── [id]/page.tsx               ← Detail + Margenkalkulation
├── shipments/page.tsx              ← Sendungen / Logistik
├── deals/page.tsx                  ← CRM / Verkaufsgespräche
├── analytics/page.tsx              ← ML-Vorhersagen (Preis, Fracht)
├── reports/page.tsx                ← Berichte
├── sentiment/page.tsx              ← Sentiment-Analyse nach Region
├── news/page.tsx                   ← Kaffee-News Feed
├── graph/page.tsx                  ← Wissensgraph (Entitäts-Verlinkungen)
├── ml/page.tsx                     ← ML-Modell-Verwaltung
├── dedup/page.tsx                  ← Deduplizierung (Betrieb)
├── ops/page.tsx                    ← Operationen / Job-Übersicht
├── alerts/page.tsx                 ← System-Alerts
├── peru-sourcing/page.tsx          ← Peru Sourcing Map
├── german-sales/page.tsx           ← Deutsches Vertriebs-Dashboard
├── analyst/page.tsx                ← KI-Analyst Assistent
├── assistant/page.tsx              ← Chat-Interface
├── search/page.tsx                 ← Globale Suche
└── login/page.tsx                  ← Auth (kein AppShell-Wrapper)
```

### Wiederverwendbare Komponenten

```
apps/web/app/components/
├── AppShell.tsx                    ← Haupt-Layout: Sidebar + Topbar + Banner (Demo/Offline)
│                                     Bindet ToastProvider + CommandPalette ein
├── Sidebar.tsx                     ← Navigation, collapsible (collapsed-Prop)
├── Topbar.tsx                      ← Suchfeld, Logout, User-Info
├── CommandPalette.tsx              ← ⌘K Schnellnavigation (global, in AppShell)
├── ToastProvider.tsx               ← Toast-System. useToast() Hook exportieren.
│                                     Typen: "success" | "error" | "warning" | "info"
├── Breadcrumb.tsx                  ← Breadcrumb-Navigation für Detailseiten
├── Badge.tsx                       ← Status-Badges (variant="success"|"warning"|"danger"|"info")
├── EmptyState.tsx                  ← Leere Zustände + SkeletonRows für Ladeanimation
├── ErrorPanel.tsx                  ← Fehleranzeige. Props: message, onRetry, compact, style
├── Pagination.tsx                  ← Tabellen-Pagination. usePagination() Hook exportiert.
└── MarketPriceWidget.tsx           ← Marktpreis-Anzeige
```

---

## CSS-System

Kein Tailwind. Alles über CSS Custom Properties in `globals.css`.

### Wichtige Design-Token-Gruppen

```css
--color-primary / --color-primary-text     ← Hauptfarbe + Text darauf
--color-surface / --color-bg-subtle        ← Hintergründe
--color-border / --color-border-strong     ← Rahmen
--color-text / --color-text-muted          ← Texte
--color-success/warning/danger/info        ← Status-Farben (je auch -subtle, -border)
--space-1 bis --space-16                   ← Abstands-Skala
--font-size-xs bis --font-size-2xl         ← Schriftgrößen
--radius-sm/md/lg/xl                       ← Border-Radius
--shadow-sm/md/lg/xl                       ← Schatten
```

### Häufig verwendete CSS-Klassen

```css
/* Layout */
.page           ← Seiten-Wrapper (padding, max-width)
.pageHeader     ← Titel + Aktionen oben
.pageActions    ← Button-Gruppe rechts im Header
.panel          ← Karte/Box mit Border + Radius
.panelHeader    ← Panel-Kopf mit Titel
.panelTitle     ← Panel-Titel-Text
.tableWrap      ← Scroll-Container für Tabellen
table.table     ← Standard-Tabelle
.fieldGrid2     ← 2-spaliges Formular-Grid

/* Status */
.badge.success/.warning/.danger/.info    ← Status-Badges
.alert.ok/.bad                           ← Inline-Alerts

/* Buttons */
.btn            ← Standard-Button
.btnPrimary     ← Primär-Button
.btnSm          ← Kleiner Button

/* Typografie */
.h1 / .h2       ← Überschriften
.muted          ← Gedämpfter Text
.mono           ← Monospace
```

---

## Wichtige Regeln (für KI-Assistenten)

1. **Typen:** Immer aus `app/types/index.ts` importieren, nie inline definieren.
2. **API-Aufrufe:** Immer über `app/services/*.service.ts` oder `app/hooks/use*.ts`, nie direktes `apiFetch` in Komponenten.
3. **Fehler:** `toErrorMessage(error)` aus `app/utils/error.ts` verwenden. Versteht `ApiError`.
4. **Toast:** `useToast()` aus `app/components/ToastProvider.tsx`. Kein `alert()` oder `console.error` für User-Feedback.
5. **Demo-Modus:** Jeder neue API-Aufruf braucht `if (isDemoMode()) return;` als ersten Guard.
6. **CSS:** Keine Inline-Styles außer für dynamische Werte. Neue Klassen in `globals.css` definieren.
7. **Seiten-Struktur:** `<div className="page">` → `<div className="pageHeader">` → `<div className="panel">`. Kein doppeltes Wrapping.
8. **Empty States:** Wenn Daten leer sind, `<EmptyState>` aus `app/components/EmptyState.tsx` verwenden.
9. **Fehler-Anzeige:** `<ErrorPanel>` für Fehler mit Retry-Button. `compact`-Prop für Inline-Einsatz.
10. **Sprache:** Alle UI-Texte auf Deutsch. Variablennamen, Kommentare und Code auf Englisch.

---

## Backend-Verbindung

Das Backend ist ein **FastAPI**-Server. Vollständige Spezifikation in `ENTERPRISE_ROADBOOK.md`.

```
Standard-URL lokal:  http://localhost:8000
Über Traefik:        http://api.localhost
Umgebungsvariable:   NEXT_PUBLIC_API_URL (in apps/web/.env.local)
```

### Auth-Flow

```
POST /auth/token        ← Login (form-data: username + password)
POST /auth/refresh      ← Token erneuern (wird automatisch von apiFetch() aufgerufen bei 401)
GET  /auth/me           ← Aktueller User
POST /auth/logout       ← Session beenden
```

### Erwartetes Fehlerformat vom Backend

```json
{
  "detail": "Lesbarer Fehlertext auf Deutsch",
  "code": "OPTIONAL_ERROR_CODE",
  "field": "optional_field_name"
}
```

---

## Git-Workflow

```
main                    ← Produktion (nur via PR)
develop                 ← Integrations-Branch
feature/THEMA           ← Feature-Branches (von develop)
fix/THEMA               ← Bugfix-Branches
```

Jeder PR auf `develop` durchläuft: TypeScript-Check → Lint → Build.

---

## Lokales Starten

Siehe `LOKAL_STARTEN.md` für vollständige Anleitung. Kurzversion:

```bash
# Frontend
cd apps/web && pnpm dev        # http://localhost:3000

# Backend (im Backend-Verzeichnis)
uvicorn main:app --reload      # http://localhost:8000

# Demo-Login (kein Backend nötig)
# E-Mail: demo@coffeestudio.de
# Passwort: demo
```
