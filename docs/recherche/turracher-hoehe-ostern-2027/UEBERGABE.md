# Übergabe — Stand nach Abschluss beider Recherche-Workflows

Diese Datei ist der Einstiegspunkt, wenn du lokal weiterarbeitest. Sie sagt, was gemacht wurde,
was belegt ist, was offen ist und wie du weitermachst.

## Was passiert ist

Zwei Agenten-Workflows mit zusammen **82 Agenten**, 3.653 Werkzeugaufrufen und 17,4 Mio. Tokens
über 10 Stunden Laufzeit, plus direkte Abfragen über Booking.com, Trivago und eine Kartensuche.

| Workflow | Agenten | Ergebnis |
|---|---|---|
| Portale, Verzeichnisse, Einzelprüfung, Kontext | 50 | 753 Rohtreffer, 597 eindeutig, 30 Objekte einzeln geprüft |
| Siedlungs-Sweep und Direktanbieter | 32 | 522 Treffer, 264 neu, 12 Anbieter tiefengeprüft, 8 Kanalvergleiche |

Das **offizielle Unterkunftsverzeichnis der Turracher Höhe ist zu 100 % erfasst** (55 Betriebe,
alle Detailseiten einzeln abgerufen).

## Das Ergebnis

Im Datensatz stehen **66 Objekte**. Bei **24** wurden die
Verfügbarkeit für 20.–27.03.2027 einzeln abgefragt und die Gesamtkosten inklusive aller Nebenkosten
durchgerechnet.

### Empfehlung

**Chalet Claassen** (Almrausch Lodge, Marktlsiedlung 347): **3.401,80 €** Gesamtkosten,
61 € je Person und Nacht. Einziges Objekt, das alle acht K.-o.-Kriterien erfüllt und zugleich
am günstigsten ist. Vier Schlafzimmer, zwei Bäder, Carport für zwei Autos, Skiraum mit beheiztem
Schuhtrockner. Die Endreinigung von 222 € **schließt Strom, Wasser und Brennholz ein** — kein
Nachzahlungsrisiko. Kostenfreie Stornierung bis 18.02.2027 über Tiscover.
Schwachpunkt: exakt acht Schlafplätze, Zustellbetten ausgeschlossen.

### Rangfolge nach Preis je Person und Nacht

| Objekt | Gesamtkosten | je Pers./Nacht | Nächte |
|---|---|---|---|
| Chalet Claassen | 3.401,80 € | 61 € | 7 |
| Atemberaubende Luxus-Lodge mit Panoramablick | 3.663,59 € | 65 € | 7 |
| Ibex panorama Lodge | 3.780,05 € | 68 € | 7 |
| Naturchalets Turracher Höhe by ALPS RESORTS | 3.847,00 € | 69 € | 7 |
| Alpenpark Turracher Höhe by ALPS RESORTS | 3.868,91 € | 69 € | 7 |
| Zirbenwald Lodge | 3.920,50 € | 70 € | 7 |
| Luxalps Turrach Alm Chalets Nr, 1–4 Grünsee | 4.166,58 € | 74 € | 7 |
| Turrach Lodges by ALPS RESORTS | 3.005,54 € | 75 € | 5 |

### Vier Erkenntnisse, die den Unterschied machen

1. **Der Anzeigepreis ist nicht der Preis.** Erst die Einzelprüfung liefert die Gesamtkosten.
   Nebenkosten machen 250 bis 600 € aus.
2. **Direktbuchung spart bis zu 19 %** — aber nicht überall. Bei ALPS RESORTS 748 € (Alpenpark)
   und 782 € (Superior Chalet 25) günstiger als das Portal. Bei Ibex und Hollmann ist das Portal
   günstiger. Pauschal gilt keine Richtung.
3. **Bäder sind der Engpass.** Das günstigste Objekt überhaupt — die Zirbenhütte für 2.412,50 €,
   43 € je Person und Nacht — hat vier Schlafzimmer, aber nur ein Bad für acht Personen.
4. **Fünf Nächte sind nicht billiger.** Turrach Lodges: 3.006 € für fünf Nächte sind 75 € je
   Person und Nacht, mehr als jedes Sieben-Nächte-Angebot. Für acht Personen sind dort sieben
   Nächte gar nicht verfügbar.

## Was offen ist

- **Saisonende der Bergbahnen 2027** ist nicht veröffentlicht. Entscheidend für die letzten Urlaubstage.
- **Skipass-, Skischul- und Anreisekosten** stehen in den Rohdaten von Workflow 1, sind aber noch
  nicht in Katalog und Karte eingearbeitet.
- **Zehn Objekte ohne Koordinaten** fehlen auf den Karten, stehen aber im Katalog.
- **19 Positionen sind geschätzt** (aus Siedlung oder Hausnummer-Nachbarschaft) und überall
  gekennzeichnet — gestrichelter Rand auf den Karten, `lage_geschaetzt: true` im GeoJSON.
- **42 Objekte haben noch keine geprüften Gesamtkosten**, nur Anzeigepreise oder gar keinen Preis.

## Lokal weiterarbeiten

```bash
git clone https://github.com/fx96515-hue/cs.git
cd cs && git checkout claude/superprompt-osterferien-unterkunft-4khvxu
cd docs/recherche/turracher-hoehe-ostern-2027
```

Alles neu bauen (Python 3, Node.js und Chromium vorausgesetzt):

```bash
cd generator && npm install
python3 geo.py        # GeoJSON, GPX, KML aus daten/objekte.json
python3 karte.py      # OSM-Karte als HTML
python3 katalog.py    # katalog.html
chromium --headless --print-to-pdf=katalog.pdf --no-pdf-header-footer katalog.html
node test-karte.mjs   # Funktionstest der Karte
```

Die Generatoren erwarten `objekte.json` im selben Verzeichnis — beim Bauen also entweder
kopieren oder die Pfade anpassen.

**Der Datensatz ist die einzige Quelle.** Alles andere wird daraus erzeugt. Wer etwas ändern will,
ändert `daten/objekte.json` und baut neu.

## Rohdaten

`daten/rohdaten/` enthält die vollständigen Agenten-Ergebnisse:

- `verifiziert.json` — die 30 Einzelprüfungen strukturiert, mit Gesamtkosten, K.-o.-Status,
  Stornobedingungen und Schwachpunkten
- `wf2_kandidaten.json` — 59 neue Objekte mit Kapazität ab 8 Personen aus dem Siedlungs-Sweep
- `wf1_ergebnis.json.gz`, `wf2_ergebnis.json.gz` — alles, was die Agenten zurückgegeben haben

## Belastbarkeit

Zwei Kartendaten-Hinweise zur Einordnung: Kartenkacheln, Geodatendienste und Bildhosts waren in
der Rechercheumgebung auf Netzwerkebene gesperrt. Deshalb sind die PDF-Karten aus den erhobenen
Koordinaten selbst gezeichnet, und Fotos konnten nicht eingebettet werden. Die HTML-Karte umgeht
das, weil dort dein Browser die Kacheln lädt.

Alle Preise sind Stand 13.09.2026 und können sich ändern. Vor jeder Buchung neu prüfen.
