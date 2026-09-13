# Unterkunfts-Recherche Turracher Höhe — Osterferien 2027

Ergebnisse einer Recherche vom 13.09.2026. Gesichert aus einer Cloud-Session, deren
Arbeitsverzeichnis nicht dauerhaft ist.

**Fängst du hier neu an? Lies zuerst `UEBERGABE.md`.** Dort steht Empfehlung, Rangfolge,
was offen ist und wie du lokal weiterbaust.

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
| `daten/rohdaten/verifiziert.json` | Die 30 Einzelprüfungen strukturiert |
| `daten/rohdaten/wf2_kandidaten.json` | 59 neue Objekte ab 8 Personen aus dem Siedlungs-Sweep |
| `daten/rohdaten/wf*_ergebnis.json.gz` | Vollständige Agenten-Ergebnisse |

## Kernbefunde

1. **Empfehlung: Chalet Claassen**, 3.401,80 € Gesamtkosten, 61 € je Person und Nacht.
   Einziges Objekt, das alle acht K.-o.-Kriterien erfüllt und zugleich am günstigsten ist.
   Endreinigung schließt Strom, Wasser und Brennholz ein, kostenfreie Stornierung bis 18.02.2027.
2. **Der Anzeigepreis ist nicht der Preis.** Nebenkosten machen 250 bis 600 € aus. Bei 24 von
   66 Objekten sind die Gesamtkosten durchgerechnet.
3. **Direktbuchung spart bis zu 19 %** — aber nicht überall. Bei ALPS RESORTS 748 bis 782 €
   günstiger, bei Ibex und Hollmann ist das Portal günstiger.
4. **Bäder sind der Engpass.** Das günstigste Objekt überhaupt (Zirbenhütte, 2.412,50 €,
   43 €/Person/Nacht) hat vier Schlafzimmer, aber nur ein Bad für acht Personen.
5. **Fünf Nächte sind nicht billiger** — Turrach Lodges kostet auf die Nacht gerechnet mehr
   als jedes Sieben-Nächte-Angebot.

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
