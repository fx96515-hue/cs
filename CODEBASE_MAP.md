
# CoffeeStudio — Codebase Map

**Stand: 2026-03 | Version: 1.3**

Dieses Dokument ist der primäre Einstiegspunkt für KI-Assistenten (OpenAI, Copilot, Cursor etc.).
Lies es bevor du irgendetwas änderst. Es beschreibt wo was liegt und wie alles zusammenhängt.

---

## Repository-Struktur

```
cs/
├── apps/
│   └── web/                        ← Next.js 16 Frontend (einzige App)
│       ├── app/                    ← App Router (alle Seiten + Komponenten)
│       │   ├── charts/             ← Wiederverwendbare Chart-Komponenten (Recharts)
│       │   ├── components/         ← Shared UI-Komponenten
│       │   ├── hooks/              ← React Query Hooks
│       │   ├── services/           ← API Service-Layer
│       │   ├── types/              ← TypeScript-Interfaces (einzige Quelle)
│       │   └── utils/              ← Hilfsfunktionen
│       ├── lib/                    ← Shared Utilities (api.ts, queryClient.ts)
│       └── proxy.ts           ← Route-Guard (Auth, passthrough bis httpOnly-Cookie)
├── ENTERPRISE_ROADBOOK.md          ← Backend-Spezifikation + Schritt-Plan zur Produktionsreife
├── LOKAL_STARTEN.md                ← Lokales Setup, Git-Workflow, VS Code Einrichtung
├── CODEBASE_MAP.md                 ← Dieses Dokument
└── coffeestudio.code-workspace     ← VS Code Multi-Root Workspace
```

---

## Frontend: Wo was liegt

### Einstiegspunkte

| Datei | Zweck |
|---|---|
| `apps/web/lib/api.ts` | Zentraler HTTP-Client. Alle Requests laufen durch `apiFetch<T>()`. Enthält `ApiError`-Klasse, 401-Auto-Refresh, `isDemoMode()`, `getToken()`, `setToken()`. **Hier beginnt jede API-Änderung.** |
| `apps/web/proxy.ts` | Next.js Route-Guard. Matcher: `/dashboard`, `/roasters/:path*`, `/cooperatives/:path*`. Wartet auf httpOnly-Cookie (Roadbook Schritt 1). |
| `apps/web/app/layout.tsx` | Root-Layout. Bindet `QueryClientProvider`, `AppShell`, Fonts ein. |
| `apps/web/app/globals.css` | Alle CSS Custom Properties (Design-Tokens) + alle Utility-Klassen. **2235+ Zeilen.** Kein Tailwind. |
| `apps/web/next.config.mjs` | Turbopack-Config inkl. `resolveAlias` für `ErrorPanel` → `AlertError`. |

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
├── page.tsx                        ← Root-Redirect → /dashboard
├── dashboard/page.tsx              ← KPI-Übersicht, AnomalyFeedWidget, Aktivitäten
├── roasters/
│   ├── page.tsx                    ← Liste mit Filter, Pagination, CSV-Export
│   └── [id]/page.tsx               ← Detail, Bearbeiten, Archivieren
├── cooperatives/
│   ├── page.tsx                    ← Liste mit Filter, Pagination, CSV-Export
│   └── [id]/page.tsx               ← Detail, Enrichment, Website-Analyse
├── lots/
│   ├── page.tsx                    ← Kaffee-Partien Liste
│   └── [id]/page.tsx               ← Detail + Margenkalkulation
├── reports/
│   ├── page.tsx                    ← Berichte-Liste
│   └── [id]/page.tsx               ← Bericht-Detail
├── peru-sourcing/
│   ├── page.tsx                    ← Peru Sourcing Map
│   └── regions/[name]/page.tsx     ← Region-Detail
├── shipments/page.tsx              ← Sendungen / Logistik
├── deals/page.tsx                  ← CRM / Verkaufsgespräche
├── analytics/page.tsx              ← ML-Vorhersagen (Preis, Fracht) + KPI-Grid
├── sentiment/page.tsx              ← Sentiment-Analyse nach Region
├── news/page.tsx                   ← Kaffee-News Feed (Marktradar)
├── graph/page.tsx                  ← Wissensgraph (Entitäts-Verlinkungen, D3/Force)
├── ml/page.tsx                     ← ML-Modell-Verwaltung + Trainings-Status
├── dedup/page.tsx                  ← Deduplizierung (Dubletten-Erkennung)
├── ops/page.tsx                    ← Operationen / Job-Übersicht
├── alerts/page.tsx                 ← System-Alerts / Data Quality Flags
├── german-sales/page.tsx           ← Deutsches Vertriebs-Dashboard
├── analyst/page.tsx                ← KI-Analyst Chat-Interface (neu gestaltet)
│                                     Layout: chatLayout → chatPanel → chatMessages + chatInputBar
│                                     POST /analyst/ask → { answer, sources[] }
│                                     GET  /analyst/status → { available, provider, model }
│                                     TypingIndicator, SourceChip, Beispiel-Fragen
│                                     Alle Klassen aus globals.css (.chatMsgRow, .chatBubble, ...)
├── assistant/page.tsx              ← Generisches Chat-Interface
├── search/page.tsx                 ← Globale semantische Suche
│                                     POST /search → { query, entity_type, results[], total }
│                                     GET  /search/similar/{entity_type}/{id} → SimilarEntity[]
└── login/page.tsx                  ← Auth (kein AppShell-Wrapper)
```

### Wiederverwendbare Komponenten

```
apps/web/app/components/
├── AppShell.tsx                    ← Haupt-Layout: Sidebar + Topbar + Banner (Demo/Offline)
│                                     Bindet ToastProvider + CommandPalette ein
│                                     <main className="page"> ist der Seiten-Container
├── Sidebar.tsx                     ← Navigation, collapsible (collapsed-State intern)
├── Topbar.tsx                      ← Suchfeld, Logout, User-Info
├── CommandPalette.tsx              ← ⌘K Schnellnavigation (global, in AppShell)
├── ToastProvider.tsx               ← Toast-System. useToast() Hook exportiert.
│                                     Typen: "success" | "error" | "warning" | "info"
├── Breadcrumb.tsx                  ← Breadcrumb-Navigation für Detailseiten
├── Badge.tsx                       ← Status-Badges. Props: tone="ok"|"warn"|"bad"|"neutral"
├── KpiCard.tsx                     ← KPI-Karte für Dashboard/Analytics
├── EmptyState.tsx                  ← Leere Zustände + SkeletonRows für Ladeanimation
├── AlertError.tsx                  ← Fehleranzeige. DATEINAME: AlertError.tsx
│                                     Import: import { ErrorPanel } from "../components/AlertError"
│                                     AUCH: import { ErrorPanel } from "../components/ErrorPanel" (Alias-Stub)
│                                     Props: message, onRetry?, compact?, style?
├── ErrorPanel.tsx                  ← Alias-Stub → re-exportiert aus AlertError.tsx
│                                     Existiert damit Turbopack-Cache aufgelöst werden kann.
│                                     Neue Importe immer auf AlertError.tsx zeigen.
├── Pagination.tsx                  ← Tabellen-Pagination. usePagination() Hook exportiert.
├── AnomalyFeedWidget.tsx           ← Anomalie-Feed Widget (Dashboard)
│                                     GET /anomalies?acknowledged=false&limit=5
│                                     isDemoMode()-Guard: gibt null zurück im Demo-Modus
│                                     503/404 → disabled=true (kein Fehler, Widget versteckt)
├── MarketPriceWidget.tsx           ← Marktpreis-Anzeige Widget
├── DataQualityMini.tsx             ← Mini-Anzeige Data-Quality-Score
├── CountrySelector.tsx             ← Länder-Auswahl Dropdown
├── QueryProvider.tsx               ← React Query Client Provider
└── Nav.tsx                         ← Alternative Navigation (Topbar-Nutzung)
```

### Charts

```
apps/web/app/charts/
├── LineChart.tsx                   ← Recharts LineChart
├── BarChart.tsx                    ← Recharts BarChart
└── PieChart.tsx                    ← Recharts PieChart
```

---

## CSS-System

Kein Tailwind. Alles über CSS Custom Properties in `globals.css` (~2450 Zeilen).

### Wichtige Design-Token-Gruppen

```css
--color-primary / --color-primary-text     ← Hauptfarbe + Text darauf
--color-surface / --color-bg-subtle        ← Hintergründe
--color-border / --color-border-strong     ← Rahmen
--color-text / --color-text-muted / --color-text-secondary
--color-success/warning/danger/info        ← Status-Farben (je auch -subtle, -border)
--color-accent / --color-accent-subtle     ← Akzentfarbe (KI, Highlights)
--space-1 bis --space-16                   ← Abstands-Skala
--font-size-xs bis --font-size-3xl         ← Schriftgrößen
--font-weight-normal/medium/semibold/bold
--line-height-relaxed                      ← 1.6 für Body-Text
--radius-sm/md/lg/xl/full                  ← Border-Radius
--shadow-sm/md/lg/xl                       ← Schatten
--transition-fast                          ← 150ms ease-in-out
```

### Häufig verwendete CSS-Klassen

```css
/* Seiten-Layout */
.page            ← <main>-Container in AppShell (flex: 1, overflow-y: auto, padding)
.content         ← Seiten-Inhalt-Wrapper (erster div in return())
.pageHeader      ← Titel + Aktionen oben (flex, space-between)
.pageActions     ← Button-Gruppe rechts im Header (= pageHeaderActions)
.chatLayout      ← Vollhöhen-Flex-Layout für Chat-Seiten (überschreibt .page overflow)

/* Panels */
.panel           ← Karte/Box mit Border + Radius + Background
.panelHeader     ← Panel-Kopf mit Titel (padding, border-bottom)
.panelTitle      ← Panel-Titel-Text (font-weight semibold)
.panelBody       ← Panel-Inhalt (padding)

/* Tabellen */
.tableWrap       ← Scroll-Container für Tabellen (overflow-x: auto)
table.table      ← Standard-Tabelle (width: 100%, border-collapse)
th / td          ← Tabellen-Zellen (padding, border-bottom)

/* Formulare */
.field           ← Formular-Feld-Wrapper
.fieldLabel      ← Label-Text
.fieldGrid2      ← 2-spaltiges Formular-Grid
.fieldStack      ← Gestapelte Formular-Felder (flex-column)
.input           ← Text-Input, Select (border, radius, padding)

/* Status */
.badge           ← Status-Badge (tone via Klasse: .ok .warn .bad .neutral)
.alert.ok        ← Grüner Inline-Alert
.alert.bad       ← Roter Inline-Alert

/* Buttons */
.btn             ← Standard-Button (border, radius, padding)
.btnPrimary      ← Primär-Button (background: primary)
.btnSm           ← Kleiner Button

/* Typografie */
.h1 / .h2        ← Überschriften
.muted / .small  ← Gedämpfter / kleiner Text
.mono            ← Monospace
.subtitle        ← Untertitel-Text

/* Listen */
.listRow         ← Zeile in einer Liste (flex, padding, border-bottom)
.listMain        ← Hauptinhalt einer Listzeile
.listTitle       ← Titel in Listzeile
.listMeta        ← Metainfos in Listzeile (muted, small)
.dot             ← Trennzeichen zwischen Meta-Elementen

/* Chat (KI-Analyst) */
.chatLayout      ← Full-Height Flex-Layout
.chatPanel       ← Chat-Bereich (flex: 1, overflow: hidden)
.chatMessages    ← Scroll-Container für Nachrichten
.chatMsgRow      ← Nachrichten-Zeile (avatar + bubble)
.chatMsgRowUser  ← User-Nachricht (row-reverse)
.chatAvatar      ← Avatar-Container (30×30, border-radius)
.chatBubble      ← Nachrichts-Bubble-Wrapper
.chatBubbleInner ← Bubble-Inhalt (padding, radius, background)
.chatBubbleUser  ← User-Bubble (primary background)
.chatBubbleAi    ← KI-Bubble (surface background, border)
.chatExamples    ← Beispiel-Fragen Bereich (center, column)
.chatExampleBtn  ← Einzelne Beispiel-Frage (border, hover)
.chatSources     ← Quellen-Links unter KI-Antwort
.chatSourceChip  ← Einzelner Quellen-Chip (pill, link)
.chatTyping      ← Typing-Indikator Container
.chatTypingDot   ← Animierter Punkt (chatDot keyframe)
.chatInputBar    ← Input-Leiste (border-top, padding)
.chatInputRow    ← Input + Senden-Button (flex)
.chatStatusBadge ← Provider-Status Pill (header)
.chatStatusDot   ← Status-Punkt (grün = online, grau = offline)
```

---

## Wichtige Regeln (für KI-Assistenten)

1. **Typen:** Immer aus `app/types/index.ts` importieren, nie inline definieren.
2. **API-Aufrufe:** Immer über `app/services/*.service.ts` oder `app/hooks/use*.ts`, nie direktes `apiFetch` in Komponenten. Ausnahme: spezifische Endpunkte die noch keinen Service haben (mit `isDemoMode()`-Guard).
3. **Fehler:** `toErrorMessage(error)` aus `app/utils/error.ts` verwenden. Versteht `ApiError`.
4. **Toast:** `useToast()` aus `app/components/ToastProvider.tsx`. Kein `alert()` oder `console.error` für User-Feedback.
5. **Demo-Modus:** Jeder neue API-Aufruf braucht `if (isDemoMode()) return;` als ersten Guard.
6. **CSS:** Keine Inline-Styles außer für dynamische Werte (z.B. `style={{ width: pct + "%" }}`). Neue Klassen in `globals.css` definieren.
7. **Seiten-Struktur:** `<div className="content">` → `<div className="pageHeader">` → `<div className="panel">`. Kein doppeltes Wrapping mit `.page` (das macht AppShell bereits).
8. **Empty States:** `<EmptyState>` aus `app/components/EmptyState.tsx` wenn Daten leer sind.
9. **Fehler-Anzeige:** `<ErrorPanel>` aus `../components/AlertError` (Datei heißt `AlertError.tsx`). `compact`-Prop für Inline-Einsatz. Immer `onRetry` übergeben wenn sinnvoll.
10. **Sprache:** Alle UI-Texte auf Deutsch. Variablennamen, Kommentare, Dateinamen auf Englisch.
11. **Table-Struktur:** `<div className="tableWrap"><table className="table">` — nicht `<div className="table"><table>`.
12. **Keine style jsx:** Kein `<style jsx>` oder `<style>` in Komponenten. Klassen in `globals.css`.
13. **KI-Chat-Seiten:** `chatLayout` als Root-Klasse statt `content` — benötigt kein umschließendes `.page`, da `chatLayout` das Overflow-Handling selbst übernimmt.

---

## Backend-Verbindung

Das Backend ist ein **FastAPI**-Server. Vollständige Spezifikation in `ENTERPRISE_ROADBOOK.md`.

```
Standard-URL lokal:  http://localhost:8000
Über Traefik:        http://api.localhost
Umgebungsvariable:   NEXT_PUBLIC_API_URL (in apps/web/.env.local)
```

### Auth-Flow (aktuell)

```
POST /auth/token        ← Login (form-data: username + password) → {access_token, token_type}
POST /auth/refresh      ← Token erneuern (automatisch durch apiFetch() bei 401)
GET  /auth/me           ← Aktueller User
POST /auth/logout       ← Session beenden
```

Token liegt aktuell in `localStorage` → Umstellung auf httpOnly-Cookie: Roadbook Schritt 1.

### Erwartetes Fehlerformat vom Backend

```json
{
  "detail": "Lesbarer Fehlertext auf Deutsch",
  "code": "OPTIONAL_ERROR_CODE",
  "field": "optional_field_name"
}
```

---

## Bekannte technische Schulden / Offene Punkte

| Problem | Ort | Fix |
|---|---|---|
| Token in `localStorage` (XSS-Risiko) | `lib/api.ts` | Roadbook Schritt 1 (httpOnly-Cookie) |
| `useEffect + fetch` statt React Query | Viele `page.tsx` | Schrittweise Migration auf Hooks (Roadbook Schritt 6) |
| `apiFetch` direkt in Seiten | Analyst, Search etc. | Service-Layer verwenden (Roadbook Schritt 5) |
| Middleware nur passthrough | `proxy.ts` | Aktivieren nach Schritt 1 |
| `ErrorPanel.tsx` als Alias-Stub | `components/` | Nach vollständiger Migration löschen |

---

## Git-Workflow

```
main / ui/v0-sandbox    ← Basis-Branch
v0/fx96515-hue-*        ← v0-Feature-Branches (PR auf Basis-Branch)
feature/THEMA           ← Manuelle Feature-Branches (von main/develop)
fix/THEMA               ← Bugfix-Branches
```

---

## Lokales Starten

Siehe `LOKAL_STARTEN.md` für vollständige Anleitung. Kurzversion:

```bash
# Frontend
cd apps/web && pnpm dev        # http://localhost:3000

# Demo-Login (kein Backend nötig)
# E-Mail: demo@coffeestudio.de
# Passwort: demo

# Backend (FastAPI, separates Repo)
uvicorn main:app --reload      # http://localhost:8000
```


---

## Repository-Struktur

```
cs/
├── apps/
│   └── web/                        ← Next.js 16 Frontend (einzige App)
│       ├── app/                    ← App Router (alle Seiten + Komponenten)
│       ├── lib/                    ← Shared Utilities (api.ts, queryClient.ts)
│       └── proxy.ts           ← Route-Guard (Auth-Schutz aller Seiten)
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
| `apps/web/proxy.ts` | Next.js Route-Guard. Schützt alle Routen außer `/login`. Liest Token aus Cookie (httpOnly) oder localStorage. |
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
├── analyst/page.tsx                ← KI-Analyst Chat-Interface
│                                     POST /analyst/ask → { answer, sources[] }
│                                     GET  /analyst/status → { available, provider, model }
│                                     Streaming via EventSource /analyst/stream (optional)
│                                     Nachrichten-History im lokalen State (kein Backend-Storage)
│                                     Sources als klickbare Links zu /roasters/[id] etc.
├── assistant/page.tsx              ← Chat-Interface (generisch)
├── search/page.tsx                 ← Globale semantische Suche
│                                     POST /search → { query, entity_type, results[], total }
│                                     GET  /search/similar/{entity_type}/{id} → SimilarEntity[]
│                                     Unterstützte entity_type: cooperative, roaster, lot
│                                     Result: { entity_id, name, similarity_score, region, city }
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
├── AlertError.tsx                  ← Fehleranzeige. DATEINAME: AlertError.tsx (nicht ErrorPanel.tsx!)
│                                     import { ErrorPanel } from "../components/AlertError"
│                                     Props: message, onRetry?, compact?, style?
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
9. **Fehler-Anzeige:** `<ErrorPanel>` aus `../components/AlertError` (Datei heisst AlertError.tsx). `compact`-Prop für Inline-Einsatz in Panels. Immer `onRetry` übergeben wenn ein Retry sinnvoll ist.
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
---

## Backend-Ergaenzung fuer PR721 Enterprise Integration

- Aktive API-Routen liegen unter `apps/api/app/api/routes/`
- `apps/api/app/routes/` enthaelt nur Kompatibilitaetswrapper fuer alte PR721-Pfade
- Additive PR721-Provider liegen unter:
  - `apps/api/app/providers/weather.py`
  - `apps/api/app/providers/shipping_data.py`
  - `apps/api/app/providers/news_market.py`
  - `apps/api/app/providers/peru_macro.py`
- Additive PR721-Fassaden liegen unter:
  - `apps/api/app/services/data_pipeline/phase2_orchestrator.py`
  - `apps/api/app/services/orchestration/phase4_scheduler.py`
- Sichere additive Migration:
  - `apps/api/alembic/versions/0020_full_stack_data_models.py`
