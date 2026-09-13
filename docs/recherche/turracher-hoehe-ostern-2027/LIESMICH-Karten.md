# Karten und Reiseführer — Turracher Höhe, Osterferien 2027

## Reisefuehrer-Turracher-Hoehe.html — fang hier an

**Doppelklick genügt.** Reiseführer und Karte in einer Datei: oben die OpenTopoMap mit
Liften, Pisten und Höhenlinien, darunter der vollständige Katalog aller 66 Unterkünfte.
Die Nummern auf der Karte entsprechen den Katalogeinträgen.

- **Karte anklicken** → Kurzinfo mit Preis, darin ein Sprung zum Katalogeintrag
- **„Auf der Karte zeigen"** an jedem Katalogeintrag → Karte springt zum Objekt
- **Kartenstil umschaltbar**: OpenTopoMap, OpenStreetMap, CyclOSM
- **Ausweichregion** ein- und ausblendbar

### PDF mit sichtbarer Karte

Der Knopf **„Als PDF drucken"** unten rechts wartet, bis die Kacheln geladen sind, und
öffnet dann den Druckdialog. Dort „Als PDF speichern" wählen. Wichtig: In den
Druckoptionen **Hintergrundgrafiken aktivieren**, sonst bleibt die Karte weiß.

Automatisch geht es so:

```bash
npm install playwright && npx playwright install chromium
node generator/pdf-mit-karte.mjs
```

Das Skript lädt den Reiseführer, wartet auf alle Kartenkacheln und schreibt
`Reisefuehrer-Turracher-Hoehe.pdf` mit Seitenzahlen.

## Warum das PDF im Repo keine echte Karte zeigt

Die Umgebung, in der recherchiert wurde, sperrt Kartendienste auf Netzwerkebene —
OSM-Kacheln, Overpass über vier Kanäle, die OpenStreetMap-API, zwei Spiegelserver und
zwei Browser-Treiber, alles blockiert. Deshalb ist die Karte im Katalog-PDF aus den
erhobenen Koordinaten selbst gezeichnet: maßstabsgetreu, aber **ohne Gelände, Straßen
und Seen**. Sie ist eine Lageskizze, keine topografische Karte.

Auf deinem Rechner gilt die Sperre nicht. Der Reiseführer lädt die echten Kacheln,
und das Skript oben macht daraus ein PDF, in dem die Karte sichtbar ist.

## Die Dateien

| Datei | Zweck |
|---|---|
| `Reisefuehrer-Turracher-Hoehe.html` | Karte und Katalog zusammen, druckbar |
| `Turracher-Hoehe-Katalog-Ostern-2027.pdf` | Katalog mit Lageskizze, 32 Seiten |
| `Karte-Turracher-Hoehe-OSM.html` | Nur die Karte, mit Preisfilter |
| `daten/*.geojson` | geojson.io, uMap, QGIS |
| `daten/*.gpx` | Organic Maps, OsmAnd, Garmin |
| `daten/*.kml` | Google My Maps, Google Earth |

## Fünf geschätzte Positionen und vierzehn abgeleitete

19 der 56 Marker stehen auf geschätzten Koordinaten, abgeleitet aus der Siedlung oder
benachbarten Hausnummern. Sie sind überall gekennzeichnet: **gestrichelter Rand** auf
den Karten, `lage_geschaetzt: true` im GeoJSON samt Schätzbasis. Sie können einige
hundert Meter danebenliegen. Die übrigen 37 Koordinaten stammen von den Buchungsportalen.

Zehn Objekte haben gar keine Koordinaten und fehlen deshalb auf den Karten; im Katalog
stehen sie mit Adresse.

## Preise

Bei 24 Objekten sind die **Gesamtkosten** durchgerechnet — Grundpreis plus Endreinigung,
Ortstaxe, Wäsche und Energie, soweit der Anbieter sie ausweist. Bei allen übrigen stehen
**Anzeigepreise ohne Nebenkosten**; dort fehlen erfahrungsgemäß 250 bis 600 €.
Stand 13.09.2026.

Kartendaten © OpenStreetMap-Mitwirkende (ODbL). OpenTopoMap-Darstellung CC-BY-SA.
