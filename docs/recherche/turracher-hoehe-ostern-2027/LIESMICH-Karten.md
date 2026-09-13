# Kartendaten Turracher Höhe — Osterferien 2027

42 Unterkünfte, Stand 13.09.2026. Belegung 8 Personen (5 Erwachsene, 3 Kinder von 8, 10 und 12 Jahren),
Anreise 20.03.2027, mindestens 5 Nächte.

## Karte-Turracher-Hoehe-OSM.html — fang hier an

**Doppelklick genügt.** Eine fertige OpenStreetMap-Karte, die im Browser aufgeht. Leaflet ist in die
Datei eingebacken, es wird nichts nachgeladen außer den Kartenkacheln. Kein Server, keine Installation,
kein Konto.

Was drin ist:

- **42 Marker**, eingefärbt nach Eignung: je dunkler, desto besser passt das Objekt auf acht Personen
- **Klick auf einen Marker** zeigt Belegung, Schlafzimmer, Bäder, Preis für 7 und 5 Nächte, Preis je
  Person und Nacht, Kaution, Bewertung, Telefon — dazu Links zum Angebot mit Fotos, zur Direktbuchung
  und zu Street View
- **Vier Kartenstile.** Voreingestellt ist OpenTopoMap: Sie zeichnet Lifte, Pisten und Höhenlinien und
  ist für ein Skigebiet die nützlichste Darstellung. Dazu Standard-OSM, CyclOSM und Humanitarian
- **Filter nach Eignung** mit laufender Zählung je Gruppe
- **Preisschieber** — blendet alles über dem eingestellten Höchstpreis aus
- **Zwei Ansichten**: Ortsgebiet oder alle Objekte inklusive Ausweichregion
- Maßstabsbalken, Quellenangabe, druckbar (Filterleiste wird beim Drucken ausgeblendet)

Funktionstest bestanden: 42 Marker, Filter greifen, Popups öffnen, keine Skriptfehler.

## Warum diese Karte nicht im PDF steckt

Die Ausführungsumgebung dieser Recherche sperrt sämtliche Kartendienste auf Netzwerkebene:
OSM-Kacheln, die Overpass-API über vier Kanäle, die OpenStreetMap-API, zwei Spiegelserver und zwei
Browser-Treiber — alles blockiert, leer oder im Timeout. Ich konnte weder Kacheln noch OSM-Geometrie
in das PDF holen. Auf deinem Rechner gilt diese Sperre nicht, deshalb der Weg über die HTML-Datei.

Die Karte im PDF ist daher aus den erhobenen Koordinaten selbst gezeichnet — maßstabsgetreu, aber ohne
Gelände und Straßen.

## Die drei Datenformate

Für den Fall, dass du die Objekte in ein anderes Werkzeug bringen willst.

**turracher-hoehe-unterkuenfte.geojson** — https://geojson.io öffnen und Datei hineinziehen.
Ebenso für uMap (https://umap.openstreetmap.fr, dauerhaft teilbar), QGIS, Felt, kepler.gl.

**turracher-hoehe-unterkuenfte.gpx** — für Organic Maps und OsmAnd (beide OSM-basiert und
offlinefähig), Komoot, Garmin und die meisten Navigationsgeräte.

**turracher-hoehe-unterkuenfte.kml** — für Google My Maps (https://mymaps.google.com, Karte
erstellen, Importieren) und Google Earth, dort nach Eignung in ein- und ausblendbare Ebenen gruppiert.

## Wichtig: fünf geschätzte Positionen

Fünf Objekte wurden nur über die Kartensuche gefunden und haben keine verifizierten Koordinaten. Ihre
Lage ist aus benachbarten Hausnummern abgeleitet und überall gekennzeichnet — in der HTML-Karte und im
PDF durch einen **gestrichelten Rand**, im GeoJSON durch `lage_geschaetzt: true` samt Schätzbasis. Sie
können einige hundert Meter danebenliegen:

- Alpin-Hütten auf der Turracherhöhe — Turracherhöhe 141
- Turracher Zirbenlodges — Barbarasiedlung 406/411
- Chalet Kornock — Turracherhöhe 177
- BärenHütte — Barbarasiedlung 324
- Mountain lodge Chalet-Turrach — Maierbruggersiedlung 361

Alle übrigen 37 Koordinaten stammen direkt von den Buchungsportalen.

## Preise

Alle Preise sind Portal-Anzeigepreise für die gesamte Gruppe, ohne Nebenkosten (Endreinigung,
Ortstaxe, Bettwäsche, Energie). Stand 13.09.2026, Änderungen vorbehalten.

Kartendaten © OpenStreetMap-Mitwirkende (ODbL). OpenTopoMap-Darstellung CC-BY-SA.
