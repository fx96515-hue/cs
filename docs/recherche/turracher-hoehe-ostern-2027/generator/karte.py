# -*- coding: utf-8 -*-
import json, os
BASE = os.path.dirname(os.path.abspath(__file__))
gj  = json.load(open(os.path.join(BASE, "turracher-hoehe-unterkuenfte.geojson"), encoding="utf-8"))
css = open(os.path.join(BASE, "node_modules/leaflet/dist/leaflet.css"), encoding="utf-8").read()
js  = open(os.path.join(BASE, "node_modules/leaflet/dist/leaflet.js"), encoding="utf-8").read()

# Leaflet erwartet seine Marker-Bilder relativ zur CSS-Datei; wir nutzen ausschliesslich
# DivIcons, deshalb die Bildregeln entfernen, damit keine 404 entstehen.
css = css.replace("url(images/", "url(data:,#")

GJ = json.dumps(gj, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

RANG = ["Erfüllt alle Kernkriterien", "Grenzfall", "Nur auf Anfrage", "Nur über Kartensuche",
        "Belegung unverifiziert", "Im Zeitraum belegt", "Zwei Einheiten nötig",
        "Kriterium verfehlt", "Ausweichregion"]
FARBE = {"Erfüllt alle Kernkriterien": "#0d366b", "Grenzfall": "#184f95",
         "Nur über Kartensuche": "#256abf", "Belegung unverifiziert": "#256abf",
         "Zwei Einheiten nötig": "#3987e5", "Kriterium verfehlt": "#6da7ec",
         "Ausweichregion": "#9aa4ae", "Nur auf Anfrage": "#256abf", "Im Zeitraum belegt": "#3987e5"}

HTML = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Turracher Höhe – Unterkünfte Osterferien 2027</title>
<style>__LEAFLET_CSS__</style>
<style>
:root{--ink:#23201b;--mut:#6f675b;--line:#ded8cd;--surf:#fcfcfb}
*{box-sizing:border-box}
html,body{margin:0;height:100%;font:14px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink)}
#map{position:absolute;inset:0}
.panel{position:absolute;z-index:1000;background:var(--surf);border:1px solid var(--line);
  border-radius:6px;box-shadow:0 2px 14px rgba(0,0,0,.13)}
#kopf{top:12px;left:12px;max-width:330px;padding:12px 14px}
#kopf h1{margin:0 0 2px;font-size:15px;letter-spacing:-.2px}
#kopf p{margin:0;font-size:11.5px;color:var(--mut);line-height:1.45}
#steuer{top:12px;right:12px;width:236px;padding:11px 13px;max-height:calc(100% - 24px);overflow:auto}
#steuer h2{margin:0 0 7px;font-size:10px;letter-spacing:1.1px;text-transform:uppercase;color:var(--mut)}
#steuer h2:not(:first-child){margin-top:13px}
.zeile{display:flex;align-items:center;gap:7px;margin-bottom:4px;font-size:12px;cursor:pointer}
.zeile input{margin:0;flex:none;cursor:pointer}
.pkt{width:13px;height:13px;border-radius:7px;flex:none;border:1.5px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,.16)}
.zahl{margin-left:auto;color:var(--mut);font-size:10.5px;font-variant-numeric:tabular-nums}
#preis{width:100%;margin:3px 0 1px}
#preiswert{font-size:11.5px;color:var(--mut)}
.btn{display:block;width:100%;margin-top:9px;padding:6px;font:inherit;font-size:11.5px;cursor:pointer;
  background:#f1f4f8;border:1px solid var(--line);border-radius:4px;color:var(--ink)}
.btn:hover{background:#e6ecf4}
.mark{display:flex;align-items:center;justify-content:center;border-radius:50%;color:#fff;
  font-weight:700;font-size:11px;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4)}
.mark.gesch{border-style:dashed}
.leaflet-popup-content{margin:11px 13px;font-size:12.5px;line-height:1.5;max-height:330px;overflow:auto}
.leaflet-popup-content h3{margin:0 0 3px;font-size:13.5px}
.leaflet-popup-content .badge{display:inline-block;font-size:10px;padding:1px 7px;border-radius:9px;
  color:#fff;margin-bottom:7px}
.leaflet-popup-content table{border-collapse:collapse;width:100%;margin-bottom:6px}
.leaflet-popup-content th{text-align:left;font-weight:400;color:var(--mut);padding:1.5px 8px 1.5px 0;
  vertical-align:top;width:40%;font-size:11.5px}
.leaflet-popup-content td{padding:1.5px 0;vertical-align:top}
.leaflet-popup-content .warn{background:#fdf3e8;border-left:3px solid #b8860b;padding:5px 8px;
  font-size:11.5px;margin:6px 0}
.leaflet-popup-content .lk a{margin-right:9px;font-size:11.5px}
@media print{#steuer,.leaflet-control-zoom,.leaflet-control-layers{display:none}}
@media (max-width:640px){#kopf{max-width:calc(100% - 24px)}#steuer{width:calc(100% - 24px);top:auto;bottom:12px;max-height:44%}}
</style></head><body>
<div id="map"></div>
<div id="kopf" class="panel">
  <h1>Turracher Höhe — Osterferien 2027</h1>
  <p>42 Unterkünfte für 8 Personen (5 Erwachsene, 3 Kinder von 8, 10 und 12 Jahren).
  Anreise 20.03.2027, ab 5 Nächte. Stand 13.09.2026.<br>
  Preise sind Portal-Anzeigepreise für die ganze Gruppe, ohne Nebenkosten.</p>
</div>
<div id="steuer" class="panel">
  <h2>Eignung</h2><div id="gruppen"></div>
  <h2>Höchstpreis 7 Nächte</h2>
  <input type="range" id="preis" min="1600" max="7400" step="100" value="7400">
  <div id="preiswert"></div>
  <h2>Karte</h2><div id="basis"></div>
  <button class="btn" id="reset">Ortsgebiet zeigen</button>
  <button class="btn" id="alle">Alle Objekte zeigen</button>
</div>
<script>__LEAFLET_JS__</script>
<script>
const DATEN = __GEOJSON__;
const RANG  = __RANG__;
const FARBE = __FARBE__;

const karten = {
  "OpenStreetMap": L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende'}),
  "OpenTopoMap (Lifte, Pisten, Höhenlinien)": L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
    maxZoom: 17, attribution: 'Kartendaten &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende, SRTM &middot; Darstellung &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (CC-BY-SA)'}),
  "CyclOSM": L.tileLayer("https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png", {
    maxZoom: 20, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende &middot; <a href="https://www.cyclosm.org/">CyclOSM</a>'}),
  "Humanitarian": L.tileLayer("https://tile-a.openstreetmap.fr/hot/{z}/{x}/{y}.png", {
    maxZoom: 20, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende &middot; Humanitarian OSM Team'})
};

const map = L.map("map", {zoomControl:true, layers:[karten["OpenTopoMap (Lifte, Pisten, Höhenlinien)"]]});
L.control.scale({imperial:false, position:"bottomleft"}).addTo(map);

const gruppen = {}, zaehler = {};
RANG.forEach(r => { gruppen[r] = L.layerGroup().addTo(map); zaehler[r] = 0; });

const eur = v => v == null ? "—" : v.toLocaleString("de-DE",{minimumFractionDigits:2,maximumFractionDigits:2}) + " €";
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

let nr = 0; const alle = [];
DATEN.features.forEach(f => {
  const p = f.properties, [lon, lat] = f.geometry.coordinates;
  const grp = RANG.includes(p.eignung) ? p.eignung : "Belegung unverifiziert";
  zaehler[grp]++; nr++;
  const farbe = FARBE[grp], gross = grp === "Erfüllt alle Kernkriterien";
  const d = gross ? 30 : 25;
  const m = L.marker([lat, lon], {
    icon: L.divIcon({className:"", iconSize:[d,d], iconAnchor:[d/2,d/2],
      html:`<div class="mark${p.lage_geschaetzt ? " gesch" : ""}" style="width:${d}px;height:${d}px;background:${farbe};font-size:${gross?12:11}px">${nr}</div>`}),
    title: p.title, zIndexOffset: gross ? 900 : 0
  });
  const r = [];
  const add = (k,v) => { if (v != null && v !== "") r.push(`<tr><th>${k}</th><td>${v}</td></tr>`); };
  add("Typ", esc(p.typ)); add("Ort", esc(p.ort));
  if (p.max_personen) add("Belegung", `max. ${p.max_personen} Pers.`
      + (p.schlafzimmer ? ` &middot; ${p.schlafzimmer} SZ` : "")
      + (p.baeder ? ` &middot; ${p.baeder} Bäder` : ""));
  if (p.preis_7_naechte_eur) add("7 Nächte", `<b>${eur(p.preis_7_naechte_eur)}</b><br><span style="color:#6f675b">${p.eur_pro_person_nacht} € je Person und Nacht</span>`);
  if (p.preis_5_naechte_eur) add("5 Nächte", eur(p.preis_5_naechte_eur));
  if (p.kaution_eur) add("Kaution", p.kaution_eur + " €");
  if (p.bewertung) add("Bewertung", `${String(p.bewertung).replace(".",",")} aus ${p.bewertungen} (${esc(p.quelle)})`);
  if (p.telefon) add("Telefon", esc(p.telefon));
  const lk = [`<a href="${esc(p.url)}" target="_blank" rel="noopener">Angebot mit Fotos</a>`];
  if (p.direktbuchung) lk.push(`<a href="${esc(p.direktbuchung)}" target="_blank" rel="noopener">Direkt buchen</a>`);
  lk.push(`<a href="https://www.google.com/maps/search/?api=1&query=${lat},${lon}" target="_blank" rel="noopener">Street View</a>`);
  m.bindPopup(
    `<h3>${nr}. ${esc(p.title)}</h3><span class="badge" style="background:${farbe}">${esc(grp)}</span>`
    + `<table>${r.join("")}</table>`
    + (p.lage_geschaetzt ? `<div class="warn"><b>Lage geschätzt.</b> ${esc(p.schaetzbasis || "")} Kann einige hundert Meter abweichen.</div>` : "")
    + `<div class="lk">${lk.join("")}</div>`, {maxWidth:330});
  m.addTo(gruppen[grp]);
  alle.push({m, grp, preis: p.preis_7_naechte_eur});
});

// Legende und Filter
const gdiv = document.getElementById("gruppen");
RANG.forEach(r => {
  if (!zaehler[r]) return;
  const l = document.createElement("label"); l.className = "zeile";
  l.innerHTML = `<input type="checkbox" checked data-g="${r}">
    <span class="pkt" style="background:${FARBE[r]}"></span><span>${r}</span>
    <span class="zahl">${zaehler[r]}</span>`;
  gdiv.appendChild(l);
});
const bdiv = document.getElementById("basis");
Object.keys(karten).forEach((k, i) => {
  const l = document.createElement("label"); l.className = "zeile";
  l.innerHTML = `<input type="radio" name="basis" ${i === 1 ? "checked" : ""} data-b="${k}"><span>${k}</span>`;
  bdiv.appendChild(l);
});

const preisSchieber = document.getElementById("preis"), preisText = document.getElementById("preiswert");
function anwenden() {
  const an = new Set([...document.querySelectorAll('[data-g]')].filter(c => c.checked).map(c => c.dataset.g));
  const max = +preisSchieber.value;
  const offen = max >= +preisSchieber.max;
  preisText.textContent = offen ? "kein Limit" : "bis " + max.toLocaleString("de-DE") + " €";
  let sicht = 0;
  RANG.forEach(r => gruppen[r] && gruppen[r].clearLayers());
  alle.forEach(o => {
    const zeigen = an.has(o.grp) && (offen || o.preis == null || o.preis <= max);
    if (zeigen) { o.m.addTo(gruppen[o.grp]); sicht++; }
  });
  document.querySelectorAll('[data-g]').forEach(c => {
    const n = alle.filter(o => o.grp === c.dataset.g && (offen || o.preis == null || o.preis <= max)).length;
    c.closest(".zeile").querySelector(".zahl").textContent = n;
  });
}
document.getElementById("steuer").addEventListener("change", e => {
  if (e.target.dataset.b) {
    Object.values(karten).forEach(l => map.removeLayer(l));
    karten[e.target.dataset.b].addTo(map);
  } else anwenden();
});
preisSchieber.addEventListener("input", anwenden);

const punkt = f => [f.geometry.coordinates[1], f.geometry.coordinates[0]];
const grenzenAlle = L.latLngBounds(DATEN.features.map(punkt));
const ortsObjekte = DATEN.features.filter(f => f.properties.zone === 1 || f.properties.zone === 2);
const grenzenOrt  = L.latLngBounds((ortsObjekte.length ? ortsObjekte : DATEN.features).map(punkt));
function zeigeOrt()  { map.fitBounds(grenzenOrt,  {padding:[70,70]}); }
function zeigeAlle() { map.fitBounds(grenzenAlle, {padding:[50,50]}); }
document.getElementById("reset").addEventListener("click", zeigeOrt);
document.getElementById("alle").addEventListener("click", zeigeAlle);
zeigeOrt(); anwenden();
window.__bereit = true;
</script></body></html>"""

HTML = (HTML.replace("__LEAFLET_CSS__", css)
            .replace("__LEAFLET_JS__", js)
            .replace("__GEOJSON__", GJ)
            .replace("__RANG__", json.dumps(RANG, ensure_ascii=False))
            .replace("__FARBE__", json.dumps(FARBE, ensure_ascii=False)))
out = os.path.join(BASE, "Karte-Turracher-Hoehe-OSM.html")
open(out, "w", encoding="utf-8").write(HTML)
print(f"geschrieben: {len(HTML)/1024:.0f} KB, {len(gj['features'])} Marker")
