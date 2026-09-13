# Unterkunfts-Recherche Turracher Höhe — Osterferien 2027

Ergebnisse einer Recherche vom 13.09.2026. Gesichert aus einer Cloud-Session, deren
Arbeitsverzeichnis nicht dauerhaft ist.

## Suchauftrag

| | |
|---|---|
| Zielgebiet | Turracher Höhe, 1.763 m, Grenze Kärnten/Steiermark, Österreich |
| Anreise | Samstag, 20.03.2027 |
| Aufenthalt | 7 Nächte bevorzugt, mindestens 5 |
| Belegung | 8 Personen: 5 Erwachsene, 3 Kinder (8, 10, 12 Jahre) |
| Schulferien | Osterferien Bayern 2027: 22.03.–02.04.2027 (verifiziert) |
| Kalenderlage | Karwoche, Karfreitag 26.03.2027, Ostersonntag 28.03.2027 |

## Ergebnisse

| Datei | Inhalt |
|---|---|
| `Turracher-Hoehe-Katalog-Ostern-2027.pdf` | 19 Seiten, 42 Objekte im Katalogformat mit Lagekarte je Eintrag, Übersichtskarte, Preisverteilung, Register, 276 klickbare Links |
| `Karte-Turracher-Hoehe-OSM.html` | Fertige OpenStreetMap-Karte, Doppelklick genügt. Leaflet eingebacken, lädt nur Kacheln nach |
| `LIESMICH-Karten.md` | Anleitung zu Karte und Datenformaten |

## Daten

| Datei | Inhalt |
|---|---|
| `daten/objekte.json` | Der Datensatz, aus dem alles erzeugt wird |
| `daten/turracher-hoehe-unterkuenfte.geojson` | Für geojson.io, uMap, QGIS |
| `daten/turracher-hoehe-unterkuenfte.gpx` | Für Organic Maps, OsmAnd, Garmin |
| `daten/turracher-hoehe-unterkuenfte.kml` | Für Google My Maps, Google Earth |
| `daten/ota-rohdaten-turrach.md` | Rohbefunde der Portalabfragen, inklusive Korrekturen |

## Kernbefunde

1. **Bäder sind der Engpass, nicht Betten.** Von 14 im Detail abgefragten Häusern nehmen
   nur 6 acht Personen in einer Einheit auf. Vier scheitern an einem einzigen Bad.
2. **Eignung kostet keinen Aufschlag.** Median der voll geeigneten Objekte 3.858 €,
   Median der Gruppe mit unverifizierter Belegung 4.026 € — die sichere Wahl ist im
   Mittel rund 170 € günstiger.
3. **Sieben Nächte sind pro Nacht billiger als fünf.** 573 €/Nacht gegen 550 €/Nacht.
4. **Fünf Häuser stehen auf keinem Buchungsportal**, nur über die Kartensuche auffindbar.

## Reproduzieren

Voraussetzungen: Python 3, Node.js, Chromium.

```bash
cd generator
npm install                  # leaflet, pdfjs-dist
python3 geo.py               # GeoJSON, GPX, KML aus objekte.json
python3 karte.py             # HTML-Karte
python3 katalog.py           # katalog.html
chromium --headless --print-to-pdf=katalog.pdf --no-pdf-header-footer katalog.html
```

Die Generatoren erwarten `objekte.json` im selben Verzeichnis.

## Grenzen der Daten

- Preise sind **Portal-Anzeigepreise** ohne Nebenkosten. Belegt sind nur zwei:
  Ortstaxe 2,50 €/Erwachsener/Nacht beim Alpenpark Turrach, Strom 0,25 €/kWh nach
  Verbrauch beim Appartementhaus.
- Bei 16 Objekten ist die zulässige Belegung nicht verifiziert.
- Fünf Positionen sind aus Hausnummern-Nachbarschaft geschätzt, überall gekennzeichnet.
- Das Saisonende der Bergbahnen für 2027 ist noch nicht veröffentlicht.
- Kartenkacheln, Geodatendienste und Bildhosts waren in der Rechercheumgebung gesperrt;
  die PDF-Karten sind daher aus den erhobenen Koordinaten selbst gezeichnet.

Kartendaten © OpenStreetMap-Mitwirkende (ODbL). OpenTopoMap-Darstellung CC-BY-SA.
