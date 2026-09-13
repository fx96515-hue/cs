# -*- coding: utf-8 -*-
import json, os, html
BASE=os.path.dirname(os.path.abspath(__file__))
D=json.load(open(os.path.join(BASE,"objekte.json"),encoding="utf-8"))
OBJ=D["objekte"]

FARBE={"ok":"#0d366b","grenzwertig":"#184f95","neu":"#256abf","unklar":"#256abf",
       "zwei":"#3987e5","ko":"#6da7ec","fallback":"#9aa4ae","anfrage":"#256abf","belegt":"#3987e5"}
LABEL={"ok":"Erfüllt alle Kernkriterien","grenzwertig":"Grenzfall",
       "neu":"Nur über Kartensuche","unklar":"Belegung unverifiziert",
       "zwei":"Zwei Einheiten nötig","ko":"Kriterium verfehlt","fallback":"Ausweichregion","anfrage":"Nur auf Anfrage","belegt":"Im Zeitraum belegt"}
def eur(v): return "—" if v is None else f"{v:,.2f} €".replace(",","X").replace(".",",").replace("X",".")

mitGeo=[o for o in OBJ if o.get("lat")]
ohne =[o for o in OBJ if not o.get("lat")]

def beschreibung(o, br="\n"):
    t=[f"{LABEL[o['status']]}", f"Typ: {o['typ']}"]
    adr=" ".join(x for x in [o.get("adresse",""),o.get("plz",""),o.get("ort","")] if x)
    if adr: t.append(f"Adresse: {adr}")
    if o.get("max"):
        s=f"Belegung: max. {o['max']} Personen"
        if o.get("sz"): s+=f", {o['sz']} Schlafzimmer"
        if o.get("bad"): s+=f", {o['bad']} Bäder"
        t.append(s)
    if o.get("p7"): t.append(f"7 Nächte: {eur(o['p7'])}  ({o['p7']/7/8:.0f} € je Person und Nacht)")
    if o.get("p5"): t.append(f"5 Nächte: {eur(o['p5'])}")
    if o.get("kaution"): t.append(f"Kaution: {o['kaution']} €")
    if o.get("taxe"): t.append(f"Ortstaxe: {o['taxe']}")
    if o.get("rating"): t.append(f"Bewertung: {str(o['rating']).replace('.',',')} aus {o['reviews']} ({o['quelle']})")
    if o.get("google"): t.append(f"Google: {o['google']}")
    if o.get("tel"): t.append(f"Telefon: {o['tel']}")
    if o.get("hinweis"): t.append(o["hinweis"])
    if o.get("lat_geschaetzt"):
        t.append("ACHTUNG Lage geschätzt, nicht verifiziert. Basis: " + o.get("schaetzbasis",""))
    t.append(f"Angebot: {o['url']}")
    if o.get("direkt"): t.append(f"Direkt: {o['direkt']}")
    return br.join(t)

# ---------- GeoJSON (simplestyle: geojson.io, uMap, Felt, Mapbox) ----------
fc={"type":"FeatureCollection",
    "properties":{"name":"Turracher Höhe – Unterkünfte Osterferien 2027",
                  "beschreibung":"8 Personen (5 Erwachsene, 3 Kinder), Anreise 20.03.2027, ab 5 Nächte. Stand 13.09.2026.",
                  "quellen":"Booking.com, Trivago, Kartensuche"},
    "features":[]}
for o in mitGeo:
    fc["features"].append({
      "type":"Feature",
      "geometry":{"type":"Point","coordinates":[round(o["lon"],6),round(o["lat"],6)]},
      "properties":{
        "title":o["name"], "name":o["name"], "description":beschreibung(o),
        "eignung":LABEL[o["status"]], "typ":o["typ"], "ort":o["ort"], "zone":o["zone"],
        "max_personen":o.get("max"), "schlafzimmer":o.get("sz"), "baeder":o.get("bad"),
        "preis_7_naechte_eur":o.get("p7"), "preis_5_naechte_eur":o.get("p5"),
        "eur_pro_person_nacht":round(o["p7"]/7/8,1) if o.get("p7") else None,
        "bewertung":o.get("rating"), "bewertungen":o.get("reviews"),
        "kaution_eur":o.get("kaution"), "telefon":o.get("tel"),
        "url":o["url"], "direktbuchung":o.get("direkt"), "quelle":o["quelle"],
        "lage_geschaetzt": bool(o.get("lat_geschaetzt")),
        "schaetzbasis": o.get("schaetzbasis"),
        "marker-color":FARBE[o["status"]],
        "marker-size":"medium" if o["status"] in ("ok","grenzwertig") else "small",
        "marker-symbol":"lodging"}})
open(os.path.join(BASE,"turracher-hoehe-unterkuenfte.geojson"),"w",encoding="utf-8").write(
    json.dumps(fc,ensure_ascii=False,indent=1))

# ---------- GPX (Organic Maps, OsmAnd, Garmin, Komoot) ----------
g=['<?xml version="1.0" encoding="UTF-8"?>',
   '<gpx version="1.1" creator="Unterkunftsrecherche Turracher Hoehe" xmlns="http://www.topografix.com/GPX/1/1">',
   '<metadata><name>Turracher Höhe – Unterkünfte Osterferien 2027</name>',
   '<desc>8 Personen, Anreise 20.03.2027, ab 5 Nächte. Stand 13.09.2026.</desc></metadata>']
for o in mitGeo:
    g.append(f'<wpt lat="{o["lat"]:.6f}" lon="{o["lon"]:.6f}">')
    g.append(f'  <name>{html.escape(o["name"])}</name>')
    g.append(f'  <desc>{html.escape(beschreibung(o, " | "))}</desc>')
    g.append(f'  <link href="{html.escape(o["url"])}"><text>Angebot</text></link>')
    g.append('  <sym>Lodging</sym><type>Unterkunft</type></wpt>')
g.append('</gpx>')
open(os.path.join(BASE,"turracher-hoehe-unterkuenfte.gpx"),"w",encoding="utf-8").write("\n".join(g))

# ---------- KML (Google My Maps, Google Earth) ----------
k=['<?xml version="1.0" encoding="UTF-8"?>',
   '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
   '<name>Turracher Höhe – Unterkünfte Osterferien 2027</name>',
   '<description>8 Personen, Anreise 20.03.2027, ab 5 Nächte. Stand 13.09.2026.</description>']
for st,c in FARBE.items():
    abgr="ff"+c[5:7]+c[3:5]+c[1:3]
    k.append(f'<Style id="s_{st}"><IconStyle><color>{abgr}</color><scale>1.1</scale>'
             '<Icon><href>http://maps.google.com/mapfiles/kml/shapes/lodging.png</href></Icon>'
             f'</IconStyle><LabelStyle><color>{abgr}</color></LabelStyle></Style>')
from collections import defaultdict
grp=defaultdict(list)
for o in mitGeo: grp[o["status"]].append(o)
for st in ["ok","grenzwertig","anfrage","neu","unklar","belegt","zwei","ko","fallback"]:
    if not grp[st]: continue
    zusatz = " (Lage geschätzt)" if st == "neu" else ""
    k.append(f'<Folder><name>{LABEL[st]}{zusatz}</name>')
    for o in grp[st]:
        k.append('<Placemark>')
        k.append(f'<name>{html.escape(o["name"])}</name>')
        k.append(f'<description><![CDATA[{beschreibung(o,"<br>")}]]></description>')
        k.append(f'<styleUrl>#s_{st}</styleUrl>')
        k.append(f'<Point><coordinates>{o["lon"]:.6f},{o["lat"]:.6f},0</coordinates></Point>')
        k.append('</Placemark>')
    k.append('</Folder>')
k.append('</Document></kml>')
open(os.path.join(BASE,"turracher-hoehe-unterkuenfte.kml"),"w",encoding="utf-8").write("\n".join(k))

print(f"GeoJSON/GPX/KML: {len(mitGeo)} Objekte mit Koordinaten")
print(f"ohne Koordinaten ({len(ohne)}): " + "; ".join(f"{o['name']} – {o.get('adresse','?')}" for o in ohne))
