# CoffeeStudio Enterprise – Benutzerhandbuch

## 1. Einführung

### Was ist CoffeeStudio?

CoffeeStudio Enterprise ist eine umfassende Software-Plattform für den professionellen Kaffeehandel zwischen Peru und Deutschland/Europa. Die Plattform unterstützt den gesamten Beschaffungs- und Vertriebsprozess:

- **Peru-Einkauf**: Verwaltung von Kooperativen, Qualitätsbewertung, Sourcing-Intelligence
- **Deutscher Vertrieb**: CRM für Röstereien, Sales-Pipeline, Kontaktmanagement
- **Logistics & Deals**: Sendungsverfolgung, Margenrechner, Lot-Management
- **Analytics**: Machine Learning für Preis- und Kostenvorhersagen
- **Marktdaten**: Automatische FX-Kurse, Kaffeepreise, News-Radar

### Zielgruppe

Dieses Handbuch richtet sich an:
- Kaffee-Einkäufer und Trader
- Vertriebsmitarbeiter im Specialty Coffee Bereich
- Operations-Manager
- Geschäftsführung und Analysten

Technische Vorkenntnisse sind nicht erforderlich. Die Bedienung erfolgt über eine moderne Web-Oberfläche.

### Überblick über die Funktionen

CoffeeStudio vereint mehrere Systeme in einer Plattform:
- **Datenbank** für Kooperativen und Röstereien
- **CRM-System** für Kundenbeziehungen
- **Logistics-Tracking** für Sendungen
- **Business Intelligence** mit ML-Vorhersagen
- **Market Intelligence** mit automatischen News-Updates
- **Enterprise-Stack** mit Monitoring und Workflows

---

## 2. Systemvoraussetzungen

### Hardware & Software

**Betriebssystem**: Windows 11 (empfohlen)

**Erforderliche Software**:
- **Docker Desktop** für Windows (mit WSL2)
- **Git** (optional, für Updates)
- **Webbrowser**: Chrome, Edge oder Firefox (aktuellste Version)

**Empfohlene Hardware**:
- Prozessor: Intel Core i5 oder AMD Ryzen 5 (oder besser)
- RAM: Mindestens 8 GB (16 GB empfohlen)
- Festplatte: 20 GB freier Speicherplatz
- Internetverbindung: Breitband (für API-Zugriffe und Updates)

### Docker Desktop Installation

1. Docker Desktop von [docker.com](https://www.docker.com/products/docker-desktop/) herunterladen
2. Installationsdatei ausführen und den Anweisungen folgen
3. Nach Installation Docker Desktop starten
4. In den Einstellungen WSL2-Integration aktivieren
5. Docker läuft im Hintergrund und startet automatisch mit Windows

---

## 3. Installation & Start

### Repository klonen (optional)

Falls Sie das Repository noch nicht haben:

```powershell
git clone https://github.com/fx96515-hue/coffeestudio-platform.git
cd coffeestudio-platform
```

### Schnellstart mit PowerShell-Skript

1. **PowerShell als Administrator öffnen**
2. **In das Projektverzeichnis wechseln**:
   ```powershell
   cd pfad\zu\coffeestudio-platform
   ```
3. **Start-Skript ausführen**:
   ```powershell
   .\run_windows.ps1
   ```

Das Skript:
- Startet alle Docker-Container
- Initialisiert die Datenbank
- Lädt Testdaten (optional)
- Öffnet die Web-UI

### Erster Login

Nach dem Start ist die Plattform unter folgenden URLs erreichbar:

- **Web-UI**: http://ui.localhost oder http://localhost:3000
- **API-Dokumentation**: http://api.localhost/docs oder http://localhost:8000/docs

**Standard-Zugangsdaten** (Development):
- E-Mail: `admin@example.com`
- Passwort: `secret123`

> **Hinweis**: Bei Erstinstallation muss im Backend einmalig der Bootstrap-Endpoint aufgerufen werden: `POST /auth/dev/bootstrap` (siehe API-Docs).

### Ports und URLs

Die Plattform verwendet mehrere Ports:

| Service | URL | Beschreibung |
|---------|-----|--------------|
| Frontend | http://ui.localhost:80 | Web-Oberfläche |
| Backend API | http://api.localhost/docs | FastAPI Swagger UI |
| Traefik | http://traefik.localhost/dashboard/ | Routing-Dashboard |
| Grafana | http://grafana.localhost | Monitoring |
| Prometheus | http://prom.localhost | Metriken |

---

## 4. Benutzeroberfläche

### Navigation (Sidebar)

Die Sidebar links enthält alle Hauptmenüpunkte:

#### **Übersicht** (Dashboard)
Zusammenfassung aller wichtigen KPIs, aktuelle Markdaten, News und Reports.

#### **Peru Einkauf**
Verwaltung von peruanischen Kooperativen, Regionen, Qualitätsbewertung und Sourcing-Opportunities.

#### **Vertrieb Deutschland**
CRM für deutsche Röstereien, Sales-Pipeline, Kontaktverwaltung und Nachverfolgung.

#### **Sendungen**
Tracking von Kaffeesendungen, Container-Status, ETAs und Logistics-Management.

#### **Deals & Margen**
Margenrechner, Profitabilitätsanalyse, Deal-Tracking und Lot-Management.

#### **Analytik & ML**
Machine Learning Vorhersagen für Frachtkosten und Kaffeepreise.

#### **Kooperativen**
Vollständige Liste aller Kooperativen mit Such- und Filterfunktion.

#### **Röstereien**
Vollständige Liste aller Röstereien (CRM-Datenbank).

#### **Marktradar**
Automatische News-Aggregation zu Kaffee-Themen (Peru, Specialty Coffee, etc.).

#### **Berichte**
System-Reports, Ingest-Jobs, tägliche Zusammenfassungen.

#### **Betrieb**
One-Click Workflows für Market-Refresh, News-Updates und Discovery-Seeds.

### Topbar (Steuerzentrale)

Die Kopfleiste zeigt:
- **Titel**: "Steuerzentrale"
- **Status-Pill**: "Daten • Workflows • Qualität"
- **Logout-Button**: Abmelden

---

## 5. Funktionen im Detail

### 5.1 Übersicht / Dashboard

**Zugriff**: Sidebar → "Übersicht"

Das Dashboard zeigt:

**KPI-Karten**:
- Backend-Status (API-Gesundheit)
- Anzahl Kooperativen im System
- Anzahl Röstereien im CRM
- USD/EUR Wechselkurs (live)
- Coffee (KC) Futures-Preis

**Marktradar-Widget**:
- Neueste 6 News-Headlines
- Link zur vollständigen News-Seite

**Reports & Runs**:
- Letzte 6 System-Reports
- Status von Ingest-Jobs

**Quick Links**:
- Direktzugriff auf Kooperativen, Röstereien, Ops
- API-Dokumentation

**Nächste Schritte** (Onboarding):
- Discovery Seed ausführen
- Enrichment aktivieren
- CRM nutzen

### 5.2 Peru Einkauf

**Zugriff**: Sidebar → "Peru Einkauf"

Diese Seite ist die zentrale Anlaufstelle für das Sourcing in Peru.

**Funktionen**:

1. **Peru-Kaffeeregionen**
   - Übersicht über Anbaugebiete
   - Höhenlagen, typische Varietäten
   - Beschreibungen der Regionen

2. **Kooperativen filtern**
   - Nach Region, Mindestkapazität, Qualitäts-Score
   - Filter zurücksetzen
   
3. **Kooperativen-Verzeichnis**
   - Tabelle mit allen relevanten Informationen
   - Spalten: Name, Region, Mitglieder, Kapazität, Zertifizierungen, Qualitäts-Score, Kontakt
   - Klick auf Name → Detailseite

**Workflow**:
1. Region auswählen oder nach Score filtern
2. Kooperative identifizieren
3. Details ansehen (Klick auf Name)
4. Kontakt aufnehmen (E-Mail/Telefon)

### 5.3 Vertrieb Deutschland

**Zugriff**: Sidebar → "Vertrieb Deutschland"

CRM-System für den Vertrieb an deutsche Röstereien.

**KPI-Karten**:
- Röstereien gesamt
- In Pipeline (kontaktiert/im Gespräch)
- Qualifiziert (bereit für Angebote)
- Durchschnittlicher Vertriebs-Score

**Prioritätskontakte**:
- Top 10 Röstereien nach Sales-Fit-Score
- Direktlink zur Detailseite

**Ausstehende Nachverfolgungen**:
- Röstereien, die Follow-up benötigen
- Überfällige Kontakte hervorgehoben

**Filter**:
- Nach Stadt, Röstertyp, Min. Vertriebs-Score

**Workflow**:
1. Prioritätskontakte bearbeiten
2. Follow-ups durchführen
3. Status aktualisieren (in Detailseite)
4. Nächsten Follow-up-Termin setzen

### 5.4 Sendungen

**Zugriff**: Sidebar → "Sendungen"

Tracking und Management von Kaffeesendungen.

**KPI-Karten**:
- Sendungen gesamt
- In Transit
- Angekommen
- Gesamtgewicht

**Bald ankommend**:
- Sendungen, die in 7 Tagen ankommen
- Countdown bis ETA

**Aktive Sendungen**:
- Karten für jede Sendung in Transit
- Fortschrittsbalken
- Route, Spediteur, Container-Nummer
- Abfahrt und ETA

**Alle Sendungen (Tabelle)**:
- Vollständiger Verlauf
- Status, Gewicht, Daten

**Funktionen**:
- Sendung hinzufügen (Button oben rechts)
- Details anzeigen (pro Sendung)

### 5.5 Deals & Margen

**Zugriff**: Sidebar → "Deals & Margen"

Margenrechner und Deal-Management.

**KPI-Karten**:
- Deals gesamt
- Pipeline-Wert (in EUR)
- Durchschnittliche Marge
- Aktive Lots

**Margenrechner** (Ein/Ausblenden):
- Einkaufspreis pro kg (USD)
- Landungskosten pro kg (EUR)
- Röst- & Verpackungskosten (EUR)
- Ertragsfaktor (Grün zu Geröstet)
- Verkaufspreis pro kg (EUR)
- **Button**: "Marge berechnen"
- Ergebnis: Detaillierte Kostenaufschlüsselung, Marge in %

**Lots & Deals (Tabelle)**:
- Alle Lots im System
- Referenz, Herkunft, Sorte, Gewicht, Cupping-Score
- Status

**Workflow**:
1. Margenrechner öffnen
2. Werte eingeben
3. Marge berechnen
4. Deal basierend auf Margen erstellen
5. Lot verfolgen

### 5.6 Analytik & ML

**Zugriff**: Sidebar → "Analytik & ML"

Machine Learning Vorhersagen für Geschäftsentscheidungen.

**KPI-Karten**:
- Aktive Kooperativen
- Deutsche Röstereien
- Durchschnittliche Qualitäts-Scores
- Durchschnittliche Vertriebs-Scores

**Frachtkostenvorhersage**:
- Eingabe: Abgangs-/Zielhafen, Gewicht, Containertyp, Datum
- ML-Modell schätzt Kosten in USD
- Konfidenz-Score und Bereich
- Anzahl ähnlicher historischer Sendungen

**Kaffeepreisvorhersage**:
- Eingabe: Herkunft, Sorte, Prozess, Qualität, Cupping-Score, Prognosedatum
- ML-Modell schätzt Preis pro kg in USD
- Konfidenz-Score und Bereich
- Trend und Marktvergleich

**Workflow**:
1. Formular ausfüllen
2. "Vorhersagen" klicken
3. Ergebnis prüfen
4. Entscheidung treffen (basierend auf Vorhersage)

### 5.7 Kooperativen

**Zugriff**: Sidebar → "Kooperativen"

Vollständige Kooperativen-Datenbank mit Such- und Filterfunktion.

**Funktionen**:
- **Suche**: Nach Name, Region, Website
- **Tabelle**: Name, Region, Land, Website, SCA-Score
- **Enrichment starten**: Automatisches Anreichern von Daten (Button → Ops)
- **Details**: Klick auf Name öffnet Detailseite

**Workflow**:
1. Nach Kooperative suchen
2. Details ansehen
3. Bei Bedarf Enrichment starten (fehlende Websites, Infos)
4. Bewertung prüfen

### 5.8 Röstereien

**Zugriff**: Sidebar → "Röstereien"

CRM-Datenbank für Röstereien (hauptsächlich Deutschland).

**Funktionen**:
- **Suche**: Nach Name, Stadt, Land
- **Tabelle**: ID, Name, Ort, Land, Website
- **Discovery / Seed**: Neue Röstereien automatisch finden
- **Details**: Klick auf Name öffnet Detailseite

**Workflow**:
1. Nach Rösterei suchen
2. Details ansehen (Kontaktdaten, CRM-Infos)
3. Bei Bedarf neue Röstereien seeden (Discovery)

### 5.9 Marktradar (News)

**Zugriff**: Sidebar → "Marktradar"

Automatische News-Aggregation zu Kaffee-Themen.

**Funktionen**:
- **Filter**: Topic (z.B. "peru coffee"), Tage (1-30)
- **Refresh**: Manuelle Aktualisierung
- **Refresh (API)**: Neue News von externen Quellen abrufen
- **Ergebnisliste**: Sortiert nach Datum, mit Quelle und Topic

**Workflow**:
1. Topic eingeben (z.B. "cajamarca coffee cooperative")
2. Tage festlegen (z.B. 7)
3. "Anwenden" klicken
4. Bei Bedarf "Refresh (API)" für neue Quellen
5. News durchsehen, externe Links öffnen

**Tipp**: Für Peru z.B. "peru specialty coffee", "cajamarca coffee cooperative", "peru arabica export" verwenden.

### 5.10 Berichte

**Zugriff**: Sidebar → "Berichte"

System-Reports und Job-Protokolle.

**Funktionen**:
- Liste der generierten Reports
- Sortierung: Neueste oben
- Klick auf Report → Details
- Link zu Prometheus (Monitoring)

**Workflow**:
1. Report öffnen
2. Details prüfen (Job-Status, Fehler, etc.)
3. Bei Problemen: Ops-Seite verwenden

### 5.11 Betrieb (Operations)

**Zugriff**: Sidebar → "Betrieb"

One-Click Workflows für Systemaufgaben.

**Funktionen**:

1. **Aktualisieren**:
   - **Market-Aktualisierung**: Holt neue FX-Kurse und Kaffeepreise
   - **News-Aktualisierung**: Holt neue News für ein Topic
   - Topic-Eingabe (z.B. "peru coffee")

2. **Discovery**:
   - **Seed**: Automatisches Finden von Kooperativen/Röstereien
   - Entitätstyp: beide, Kooperative, Rösterei
   - Max. Entitäten: 1-500
   - Läuft asynchron über Celery

3. **Ausführungsprotokoll**:
   - Zeigt alle ausgeführten Aktionen mit Timestamp
   - Status: OK / ERROR

**Workflow**:
1. **Markt-Aktualisierung**: Täglich/wöchentlich ausführen
2. **News-Aktualisierung**: Bei Bedarf mit spezifischem Topic
3. **Discovery Seed**: Bei Neustart oder zur Erweiterung der Datenbank
4. Protokoll prüfen für Fehler

---

## 6. API-Dokumentation

Die vollständige API-Dokumentation ist über Swagger UI erreichbar:

**URL**: http://api.localhost/docs oder http://localhost:8000/docs

### Verfügbare Endpoints

Die API bietet 20 Router mit folgenden Hauptbereichen:

| Router | Funktion |
|--------|----------|
| `/health` | System-Gesundheit |
| `/auth` | Authentifizierung & Login |
| `/cooperatives` | Kooperativen-Verwaltung |
| `/roasters` | Röstereien-Verwaltung |
| `/discovery` | Web-Discovery & Seeding |
| `/sources` | Datenquellen |
| `/market` | Marktdaten (FX, Kaffeepreise) |
| `/reports` | System-Reports |
| `/lots` | Lot-Management |
| `/margins` | Margenberechnungen |
| `/enrich` | Datenanreicherung |
| `/dedup` | Duplikaterkennung |
| `/news` | News-Aggregation |
| `/regions` | Peru-Regionen |
| `/logistics` | Sendungsverfolgung |
| `/outreach` | CRM-Outreach |
| `/kb` | Knowledge Base |
| `/cuppings` | Cupping-Scores |
| `/ml_predictions` | ML-Vorhersagen |
| `/peru_sourcing` | Peru Sourcing Intelligence |
| `/shipments` | Sendungen |

### Authentifizierung

Die API verwendet JWT-Token-Authentifizierung:

1. **Login**: `POST /auth/login` mit E-Mail und Passwort
2. **Token erhalten**: Response enthält `access_token`
3. **Token verwenden**: Als Bearer-Token in allen Requests

**Beispiel** (curl):
```bash
# Login
curl -X POST http://api.localhost/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"secret123"}'

# API-Call mit Token
curl -X GET http://api.localhost/cooperatives \
  -H "Authorization: Bearer <TOKEN>"
```

### Rollen und Berechtigungen

Das System kennt folgende Rollen:
- **admin**: Volle Berechtigungen
- **analyst**: Lese- und Analysezugriff
- **viewer**: Nur Lesezugriff

---

## 7. Enterprise Stack

CoffeeStudio nutzt einen modernen Enterprise-Stack für Produktion.

### Traefik (Reverse Proxy)

**URL**: http://traefik.localhost/dashboard/

- Routing aller Services
- SSL-Terminierung (Produktion)
- Load Balancing
- Dashboard zeigt alle Routes

### Grafana (Monitoring Dashboard)

**URL**: http://grafana.localhost

**Standard-Zugangsdaten**:
- Benutzer: `admin`
- Passwort: `admin` (beim ersten Login ändern)

**Funktionen**:
- Visualisierung von Metriken
- Dashboards für Performance, Fehler, Requests
- Alerts und Notifications
- Integration mit Prometheus

### Prometheus (Metriken-Sammlung)

**URL**: http://prom.localhost

- Sammelt Metriken von allen Services
- Query-Interface für Ad-hoc-Analysen
- Basis für Grafana-Dashboards
- Metriken: CPU, RAM, Requests, Response-Times, Fehlerquoten

### Keycloak (IAM) - Optional

**URL**: http://keycloak.localhost

- Single Sign-On (SSO)
- User-Management
- Rollen- und Berechtigungsverwaltung
- LDAP/AD-Integration (Enterprise)

### n8n (Workflow Automation) - Optional

**URL**: http://n8n.localhost

- No-Code Workflow-Builder
- Integration mit externen APIs
- Automatisierung von Geschäftsprozessen
- Trigger, Actions, Transformations

---

## 8. Daten-Seeding

### Was ist Seeding?

Seeding ist der Prozess, bei dem Testdaten oder initiale Produktivdaten in die Datenbank geladen werden.

### Discovery Seed

**Zugriff**: Sidebar → "Betrieb" → Discovery-Bereich

Der Discovery Seed findet automatisch Kooperativen und Röstereien im Web.

**Schritte**:
1. Entitätstyp wählen: "beide", "Kooperative" oder "Rösterei"
2. Max. Anzahl festlegen (z.B. 50)
3. "Seed" klicken
4. Prozess läuft im Hintergrund (Celery)
5. Ergebnis in Protokoll prüfen

**Was passiert**:
- Web-Suche nach Kaffeekooperativen/-röstern
- Automatisches Extrahieren von Daten
- Speichern in Datenbank
- Optional: Enrichment (Website, Kontaktdaten)

### Manuelle Daten-Eingabe

**Lots**: Sidebar → "Lots"
- Formular "Neues Lot"
- Felder ausfüllen (Kooperative, Name, Gewicht, etc.)
- "Lot anlegen" klicken

**Kooperativen/Röstereien**: Über API (siehe Swagger UI)

---

## 9. Troubleshooting

### Häufige Probleme und Lösungen

#### Problem: "Docker ist nicht gestartet"

**Symptome**: `.\run_windows.ps1` schlägt fehl mit Docker-Fehler

**Lösung**:
1. Docker Desktop öffnen
2. Warten bis "Docker Desktop is running" erscheint
3. Skript erneut ausführen

---

#### Problem: "Port bereits in Verwendung"

**Symptome**: Fehler beim Start, Port 3000 oder 8000 belegt

**Lösung**:
```powershell
# Alle laufenden Container stoppen
docker stop $(docker ps -aq)

# Oder spezifischen Port finden und Prozess beenden
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

---

#### Problem: "API antwortet nicht / 404 Fehler"

**Symptome**: Frontend lädt, aber keine Daten

**Lösung**:
1. Backend-Status prüfen: http://api.localhost/docs
2. Docker-Logs prüfen:
   ```powershell
   docker logs coffeestudio_backend
   ```
3. Container neustarten:
   ```powershell
   docker-compose restart backend
   ```

---

#### Problem: "Login funktioniert nicht"

**Symptome**: "Invalid credentials" oder ähnlich

**Lösung**:
1. Bootstrap-Endpoint aufrufen:
   - Browser: http://api.localhost/docs
   - Endpoint `/auth/dev/bootstrap` → "Try it out" → "Execute"
2. Oder via curl:
   ```bash
   curl -X POST http://api.localhost/auth/dev/bootstrap
   ```
3. Mit Standard-Zugangsdaten einloggen

---

#### Problem: "Keine Daten in Kooperativen/Röstereien"

**Symptome**: Tabellen sind leer

**Lösung**:
1. Discovery Seed ausführen (Sidebar → "Betrieb")
2. Oder manuell Daten eingeben
3. Oder Datenbank-Seed über CLI:
   ```powershell
   docker-compose exec backend python -m app.cli seed
   ```

---

#### Problem: "News-Refresh funktioniert nicht"

**Symptome**: Keine neuen News nach Refresh

**Lösung**:
1. Prüfen ob externe API erreichbar ist (Firewall, Netzwerk)
2. Logs prüfen:
   ```powershell
   docker logs coffeestudio_backend | findstr news
   ```
3. Alternative Topic verwenden
4. Celery-Worker prüfen:
   ```powershell
   docker logs coffeestudio_worker
   ```

---

#### Problem: "Performance-Probleme / Langsame UI"

**Lösung**:
1. Docker Desktop RAM erhöhen:
   - Settings → Resources → Memory: 8 GB (oder mehr)
2. Nicht benötigte Container stoppen
3. Browser-Cache leeren
4. Grafana prüfen für Bottlenecks

---

#### Problem: "WSL2-Fehler unter Windows"

**Symptome**: Docker Desktop startet nicht, WSL-Fehler

**Lösung**:
1. WSL2 Update:
   ```powershell
   wsl --update
   ```
2. WSL-Integration in Docker Desktop aktivieren
3. Windows neu starten

---

#### Problem: "CORS-Fehler im Browser"

**Symptome**: Browser-Konsole zeigt CORS-Fehler

**Lösung**:
1. Prüfen ob Backend läuft: http://api.localhost/docs
2. .env-Datei prüfen: `CORS_ORIGINS` korrekt?
3. Container neustarten:
   ```powershell
   docker-compose restart backend frontend
   ```

---

### Logs und Debugging

**Container-Logs anzeigen**:
```powershell
# Alle Logs
docker-compose logs

# Nur Backend
docker-compose logs backend

# Live-Stream
docker-compose logs -f backend
```

**Datenbankzugriff**:
```powershell
# PostgreSQL Shell
docker-compose exec postgres psql -U postgres -d coffeestudio

# Tabellen anzeigen
\dt

# Daten abfragen
SELECT * FROM cooperatives LIMIT 10;
```

**Redis-Cache prüfen**:
```powershell
docker-compose exec redis redis-cli
> KEYS *
> GET <key>
```

---

## 10. Tastenkürzel & Tipps

### Browser-Shortcuts

- **Strg + K**: Globale Suche (falls implementiert)
- **Strg + R**: Seite neu laden
- **F12**: Browser Developer Tools

### Workflow-Tipps

1. **Tägliche Routine**:
   - Betrieb → Market-Aktualisierung
   - Übersicht prüfen (Dashboard)
   - Follow-ups bearbeiten (Vertrieb Deutschland)

2. **Wöchentliche Aufgaben**:
   - News-Aktualisierung mit verschiedenen Topics
   - Neue Kooperativen/Röstereien suchen (Discovery)
   - Reports durchsehen

3. **Monatliche Aufgaben**:
   - Qualitäts-Scores aktualisieren (Kooperativen)
   - Pipeline-Review (Vertrieb)
   - Analytics nutzen für Prognosen

### Produktivitäts-Tipps

- **Mehrere Tabs**: Öffnen Sie mehrere Tabs für parallele Arbeit
- **Lesezeichen**: Speichern Sie häufig genutzte Seiten
- **Filter speichern**: Notieren Sie häufig genutzte Filtereinstellungen
- **API-Integration**: Nutzen Sie die API für Bulk-Operationen
- **Grafana-Alerts**: Konfigurieren Sie Alerts für kritische Metriken

---

## 11. Support und Ressourcen

### Dokumentation

- **README.md**: Technische Setup-Anleitung
- **README_WINDOWS.md**: Windows-spezifische Anleitung
- **API-Docs**: http://api.localhost/docs
- **CHANGELOG.md**: Versions-History

### Community

- **GitHub Issues**: Bugs und Feature Requests
- **Discussions**: Fragen und Ideen austauschen

### Enterprise Support

Für Enterprise-Kunden:
- Dedizierter Support-Kanal
- Schulungen und Workshops
- Custom Feature Development
- On-Premises Installation

---

## 12. Best Practices

### Datenpflege

1. **Regelmäßige Updates**:
   - Market-Daten: Täglich
   - Kooperativen/Röstereien: Wöchentlich
   - Qualitäts-Scores: Bei neuen Informationen

2. **Datenqualität**:
   - Duplikate vermeiden (Dedup nutzen)
   - Fehlende Infos ergänzen (Enrichment)
   - Veraltete Daten archivieren

3. **Backups**:
   - Regelmäßige Datenbank-Backups
   - Export wichtiger Daten (CSV)

### Sicherheit

1. **Passwörter**:
   - Standard-Passwörter ändern
   - Sichere Passwörter verwenden
   - Passwörter regelmäßig aktualisieren

2. **Zugriffsrechte**:
   - Rollen korrekt zuweisen
   - Least-Privilege-Prinzip
   - Regelmäßige Überprüfung

3. **Updates**:
   - System aktuell halten
   - Security-Patches einspielen
   - Dependencies aktualisieren

---

## Anhang: Glossar

**Kooperative**: Zusammenschluss von Kaffeebauern zur gemeinsamen Vermarktung

**Rösterei**: Unternehmen, das grünen Kaffee röstet und verkauft

**Lot**: Charge oder Partie von Kaffee mit einheitlichen Eigenschaften

**SCA**: Specialty Coffee Association (Qualitätsstandard)

**Cupping Score**: Qualitätsbewertung von Kaffee (0-100 Punkte)

**FOB**: Free on Board (Incoterm - Lieferbedingung)

**CIF**: Cost, Insurance and Freight (Incoterm)

**ML**: Machine Learning (Maschinelles Lernen)

**KPI**: Key Performance Indicator (Kennzahl)

**CRM**: Customer Relationship Management

**Pipeline**: Vertriebsprozess / Verkaufstrichter

**Enrichment**: Automatisches Anreichern von Daten

**Seeding**: Initialer Datenimport / Testdaten laden

**Discovery**: Automatisches Finden neuer Datenquellen

---

**Version**: 1.0  
**Datum**: Februar 2026  
**Kontakt**: support@coffeestudio.com

---

*Dieses Handbuch wird kontinuierlich aktualisiert. Die neueste Version finden Sie im GitHub-Repository.*
