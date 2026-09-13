# -*- coding: utf-8 -*-
import json, os, html, re
BASE=os.path.dirname(os.path.abspath(__file__))
D=json.load(open(os.path.join(BASE,"objekte.json"),encoding="utf-8"))
META,OBJ=D["meta"],D["objekte"]
css=open(os.path.join(BASE,"node_modules/leaflet/dist/leaflet.css"),encoding="utf-8").read().replace("url(images/","url(data:,#")
js =open(os.path.join(BASE,"node_modules/leaflet/dist/leaflet.js"),encoding="utf-8").read()

RANK={"ok":0,"grenzwertig":1,"anfrage":2,"neu":2,"unklar":2,"belegt":3,"zwei":3,"ko":4,"fallback":2}
RAMP=["#0d366b","#184f95","#256abf","#3987e5","#6da7ec"]
LABEL={"ok":"Erfüllt alle Kernkriterien","grenzwertig":"Grenzfall","anfrage":"Nur auf Anfrage",
       "neu":"Nur über Kartensuche","unklar":"Belegung unverifiziert","belegt":"Im Zeitraum belegt",
       "zwei":"Zwei Einheiten nötig","ko":"Kriterium verfehlt","fallback":"Ausweichregion"}
ORDER=["ok","grenzwertig","anfrage","neu","unklar","belegt","zwei","ko","fallback"]
col=lambda o: RAMP[RANK[o["status"]]]
esc=lambda s: html.escape(str(s)) if s is not None else ""
def eur(v): return "—" if v is None else f"{v:,.2f} €".replace(",","X").replace(".",",").replace("X",".")
def kurz(s,n): 
    s=re.sub(r'\s+',' ',str(s or '')).strip(); return s[:n]+('…' if len(s)>n else '')

# Nummerierung: nach Eignung, innerhalb nach Preis je Person und Nacht
def sortkey(o): return (RANK[o["status"]], o.get("ppn") or (o["p7"]/56 if o.get("p7") else 9e9))
SORT=sorted(OBJ, key=sortkey)
for i,o in enumerate(SORT,1): o["_no"]=i

def karte_eintrag(o):
    rows=[]
    def r(k,v):
        if v not in (None,"","—"): rows.append(f"<tr><th>{k}</th><td>{v}</td></tr>")
    adr=", ".join(x for x in [o.get("adresse",""),o.get("ort","")] if x)
    r("Typ",esc(o.get("typ"))); r("Adresse",esc(adr))
    if o.get("max"): r("Belegung",f"max. {o['max']} Personen"
        + (f" · {o['sz']} Schlafzimmer" if o.get("sz") else "")
        + (f" · {o['bad']} Bäder" if o.get("bad") else ""))
    n=o.get("naechte",7)
    if o.get("gesamt"):
        r("Gesamtkosten geprüft",
          f"<b class='p'>{eur(o['gesamt'])}</b> für {n} Nächte · {o['ppn']:.0f} € je Person und Nacht")
    elif o.get("p7"):
        r("Anzeigepreis",f"<b class='p'>{eur(o['p7'])}</b> für 7 Nächte · {o['p7']/56:.0f} € je Person und Nacht"
          + " <span class='mut'>ohne Nebenkosten</span>")
    if o.get("nebenkosten"): r("Nebenkosten",esc(kurz(o["nebenkosten"],190)))
    if o.get("storno"):      r("Storno",esc(kurz(o["storno"],140)))
    if o.get("kanal"):       r("Kanal",esc(o["kanal"]))
    if o.get("rating"):      r("Bewertung",f"{str(o['rating']).replace('.',',')} aus {o['reviews']} ({esc(o['quelle'])})")
    if o.get("google"):      r("Google",esc(o["google"]))
    if o.get("tel"):         r("Telefon",esc(o["tel"]))
    lk=[]
    if o.get("url"):    lk.append(f"<a href='{esc(o['url'])}' target='_blank' rel='noopener'>Angebot mit Fotos</a>")
    if o.get("direkt"): lk.append(f"<a href='{esc(o['direkt'])}' target='_blank' rel='noopener'>Direkt buchen</a>")
    c=col(o); zeig = (f"<button class='zeig' data-no='{o['_no']}'>Auf der Karte zeigen</button>"
                      if o.get("lat") else "")
    warn = (f"<p class='warn'>Lage geschätzt: {esc(o.get('schaetzbasis',''))}</p>" if o.get("lat_geschaetzt") else "")
    schw = (f"<p class='schw'><b>Schwachpunkt:</b> {esc(kurz(o['schwaeche'],200))}</p>" if o.get("schwaeche") else "")
    return f"""<article class="karte" id="obj{o['_no']}">
 <header><span class="no" style="background:{c}">{o['_no']}</span>
  <h3>{esc(o['name'])}</h3><span class="badge" style="background:{c}">{LABEL[o['status']]}</span></header>
 <table>{''.join(rows)}</table>
 {f"<p class='note'>{esc(kurz(o.get('hinweis',''),230))}</p>" if o.get('hinweis') else ''}
 {schw}{warn}
 <p class="lk">{' · '.join(lk)} {zeig}</p></article>"""

SEK=[("ok","Erfüllt alle Kernkriterien","Acht Personen in einer Einheit, mindestens vier Schlafzimmer, mindestens zwei Bäder, Zeitraum frei. Nach Preis je Person und Nacht sortiert."),
     ("grenzwertig","Grenzfall","Nimmt acht Personen auf, verfehlt ein Kriterium knapp."),
     ("anfrage","Nur auf Anfrage","Kein öffentlicher Buchungskalender. Verfügbarkeit telefonisch klären."),
     ("neu","Nur über die Kartensuche gefunden","Auf keinem Buchungsportal gelistet. Direktanfrage nötig — und deshalb in Ferienwochen oft noch frei."),
     ("unklar","Belegung unverifiziert","Preis bekannt, zulässige Personenzahl nicht. Vor Buchung nachfragen."),
     ("belegt","Im Zeitraum belegt","Geprüft und nicht verfügbar. Bei Stornierungen kann eine Anfrage lohnen."),
     ("zwei","Zwei Einheiten nötig","Größte Einzeleinheit fasst weniger als acht Personen."),
     ("ko","Kriterium verfehlt","Dokumentiert, nicht empfohlen."),
     ("fallback","Ausweichregion","Ohne Pistenanbindung Turracher Höhe, dafür deutlich günstiger.")]

sektionen=[]
for st,titel,intro in SEK:
    g=[o for o in SORT if o["status"]==st]
    if not g: continue
    sektionen.append(f"<section class='sek'><h2>{titel} <span class='cnt'>{len(g)}</span></h2>"
                     f"<p class='intro'>{intro}</p>{''.join(karte_eintrag(o) for o in g)}</section>")

GJ=json.dumps([{"no":o["_no"],"name":o["name"],"lat":o.get("lat"),"lon":o.get("lon"),
                "st":LABEL[o["status"]],"c":col(o),"gesch":bool(o.get("lat_geschaetzt")),
                "preis":o.get("gesamt") or o.get("p7"),"ppn":o.get("ppn"),
                "gepr":bool(o.get("gesamt")),"typ":o.get("typ"),"url":o.get("url","")}
               for o in SORT if o.get("lat")], ensure_ascii=False).replace("<","\\u003c")
LEG=json.dumps([{"l":LABEL[s],"c":RAMP[RANK[s]]} for s in ORDER if any(o["status"]==s for o in OBJ)], ensure_ascii=False)

gepr=sum(1 for o in OBJ if o.get("gesamt")); top=[o for o in SORT if o["status"]=="ok" and o.get("gesamt")][0]
HTML=f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reiseführer Turracher Höhe — Osterferien 2027</title>
<style>{css}</style>
<style>
:root{{--ink:#23201b;--mut:#6f675b;--line:#ded8cd;--surf:#fcfcfb;--akz:#0d366b}}
*{{box-sizing:border-box}}
body{{margin:0;font:15px/1.6 Georgia,"Times New Roman",serif;color:var(--ink);background:#f0eee9}}
.blatt{{max-width:960px;margin:0 auto;background:#fff;padding:34px 38px 46px}}
h1,h2,h3,.sans{{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
h1{{font-size:30px;margin:0 0 4px;color:#0d1a2b;letter-spacing:-.5px}}
.sub{{color:var(--mut);font-style:italic;margin:0 0 18px}}
h2{{font-size:19px;margin:30px 0 4px;padding-bottom:6px;border-bottom:2.5px solid var(--akz);color:#0d1a2b}}
h2 .cnt{{float:right;font-size:12px;color:var(--mut);font-weight:400;background:#eef2f7;border-radius:10px;padding:2px 9px}}
.intro{{color:var(--mut);font-size:13.5px;margin:6px 0 14px}}
.fakten{{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-top:1px solid var(--line);margin-bottom:20px}}
.fakten div{{border-bottom:1px solid #eee9e0;padding:8px 12px 8px 0}}
.fakten .k{{font-family:system-ui,sans-serif;font-size:10px;letter-spacing:1.1px;text-transform:uppercase;color:#8a8275}}
.fakten .v{{font-size:15px}}
.tipp{{background:#f2f6fb;border-left:4px solid var(--akz);padding:13px 16px;margin:16px 0}}
.tipp h4{{margin:0 0 5px;font-family:system-ui,sans-serif;font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:var(--akz)}}
.tipp p{{margin:0}}
#mapwrap{{position:relative;margin:4px 0 6px}}
#map{{height:620px;border:1px solid var(--line);border-radius:4px}}
#stil{{display:flex;gap:14px;flex-wrap:wrap;font-family:system-ui,sans-serif;font-size:12.5px;margin:10px 0 4px;align-items:center}}
#stil label{{display:flex;gap:5px;align-items:center;cursor:pointer}}
#legende{{display:flex;gap:14px;flex-wrap:wrap;font-family:system-ui,sans-serif;font-size:11.5px;margin:6px 0 2px;color:var(--mut)}}
#legende span{{display:flex;gap:5px;align-items:center}}
#legende i{{width:11px;height:11px;border-radius:6px;display:inline-block}}
.mark{{display:flex;align-items:center;justify-content:center;border-radius:50%;color:#fff;font-weight:700;
  font-family:system-ui,sans-serif;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.45)}}
.mark.gesch{{border-style:dashed}}
.karte{{border:1px solid #e4ded3;border-radius:4px;padding:12px 15px;margin-bottom:12px;break-inside:avoid;page-break-inside:avoid}}
.karte header{{display:flex;align-items:center;gap:9px;margin-bottom:8px;flex-wrap:wrap}}
.karte h3{{margin:0;font-size:16px;flex:1;color:#0d1a2b}}
.no{{min-width:21px;height:21px;border-radius:11px;color:#fff;font-family:system-ui,sans-serif;font-size:11.5px;
  font-weight:700;display:inline-flex;align-items:center;justify-content:center;padding:0 5px}}
.badge{{font-family:system-ui,sans-serif;font-size:10.5px;color:#fff;padding:2.5px 9px;border-radius:10px;white-space:nowrap}}
.karte table{{width:100%;border-collapse:collapse;font-size:13.5px}}
.karte th{{text-align:left;font-weight:400;color:var(--mut);width:26%;padding:2.5px 10px 2.5px 0;
  vertical-align:top;font-family:system-ui,sans-serif;font-size:12px}}
.karte td{{padding:2.5px 0;vertical-align:top}}
.p{{color:var(--akz);font-size:16px;font-family:system-ui,sans-serif}}
.mut{{color:var(--mut);font-size:12px}}
.note{{font-size:13px;color:#4a443b;margin:8px 0 4px}}
.schw{{font-size:12.5px;color:#7a5a2a;margin:5px 0}}
.warn{{font-size:12px;color:#8a6a3b;margin:4px 0;font-style:italic}}
.lk{{margin:8px 0 0;font-size:13px}}
.lk a{{color:#184f95;margin-right:12px}}
.zeig{{font:inherit;font-size:12px;font-family:system-ui,sans-serif;background:#eef2f7;border:1px solid var(--line);
  border-radius:4px;padding:3px 10px;cursor:pointer;color:var(--akz)}}
.zeig:hover{{background:#e0e8f2}}
.fuss{{font-size:12px;color:var(--mut);border-top:1px solid var(--line);padding-top:10px;margin-top:26px}}
.druck{{position:fixed;right:16px;bottom:16px;z-index:2000;font-family:system-ui,sans-serif;font-size:13px;
  background:var(--akz);color:#fff;border:0;border-radius:6px;padding:10px 16px;cursor:pointer;box-shadow:0 3px 12px rgba(0,0,0,.3)}}
@media print{{
  body{{background:#fff}} .blatt{{max-width:none;padding:0}}
  .druck,.zeig,#stil{{display:none}}
  #map{{height:560px;page-break-inside:avoid;break-inside:avoid}}
  .leaflet-control-zoom{{display:none}}
  .sek{{page-break-before:always}}
  h2{{page-break-after:avoid}}
  a{{color:#184f95;text-decoration:none}}
  @page{{size:A4;margin:14mm 12mm}}
}}
</style></head><body>
<div class="blatt">
<h1>Turracher Höhe — Osterferien 2027</h1>
<p class="sub">Reiseführer für 8 Personen · Anreise 20. März 2027 · {len(OBJ)} Unterkünfte</p>
<div class="fakten">
 <div><div class="k">Anreise</div><div class="v">Sa 20.03.2027</div></div>
 <div><div class="k">Abreise</div><div class="v">Sa 27.03.2027</div></div>
 <div><div class="k">Belegung</div><div class="v">5 Erw. + 3 Kinder</div></div>
 <div><div class="k">Geprüfte Gesamtkosten</div><div class="v">{gepr} Objekte</div></div>
</div>
<div class="tipp"><h4>Empfehlung</h4><p><b>{esc(top['name'])}</b> — {eur(top['gesamt'])} Gesamtkosten,
 {top['ppn']:.0f} € je Person und Nacht. Einziges Objekt, das alle acht Kernkriterien erfüllt und zugleich
 am günstigsten ist. Die Endreinigung von 222 € schließt Strom, Wasser und Brennholz ein.
 Kostenfreie Stornierung bis 18.02.2027.</p></div>

<h2>Karte</h2>
<p class="intro">OpenTopoMap zeigt Lifte, Pisten und Höhenlinien. Die Nummern entsprechen den Einträgen
im Katalog. Gestrichelter Rand heißt: Lage geschätzt, nicht verifiziert.</p>
<div id="stil"></div>
<div id="mapwrap"><div id="map"></div></div>
<div id="legende"></div>
{''.join(sektionen)}
<div class="fuss">
 Stand 13.09.2026. Alle Preise für die gesamte Gruppe. Geprüfte Gesamtkosten enthalten Endreinigung,
 Ortstaxe, Wäsche und Energie, soweit der Anbieter sie ausweist; Anzeigepreise enthalten sie nicht.
 Kartendaten © OpenStreetMap-Mitwirkende (ODbL), Darstellung © OpenTopoMap (CC-BY-SA).
</div></div>
<button class="druck" id="druck">Als PDF drucken</button>
<script>{js}</script>
<script>
const D={GJ}, LEG={LEG};
const K={{
 "OpenTopoMap": L.tileLayer("https://{{s}}.tile.opentopomap.org/{{z}}/{{x}}/{{y}}.png",{{maxZoom:17,
   attribution:'Kartendaten &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende, SRTM &middot; &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (CC-BY-SA)'}}),
 "OpenStreetMap": L.tileLayer("https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",{{maxZoom:19,
   attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende'}}),
 "CyclOSM": L.tileLayer("https://{{s}}.tile-cyclosm.openstreetmap.fr/cyclosm/{{z}}/{{x}}/{{y}}.png",{{maxZoom:20,
   attribution:'&copy; OpenStreetMap-Mitwirkende &middot; CyclOSM'}})
}};
const map=L.map("map",{{layers:[K["OpenTopoMap"]],scrollWheelZoom:false}});
L.control.scale({{imperial:false}}).addTo(map);
const idx={{}};
D.forEach(o=>{{
  const gross=o.st==="Erfüllt alle Kernkriterien", d=gross?30:25;
  const m=L.marker([o.lat,o.lon],{{title:o.name,zIndexOffset:gross?900:0,
    icon:L.divIcon({{className:"",iconSize:[d,d],iconAnchor:[d/2,d/2],
      html:`<div class="mark${{o.gesch?" gesch":""}}" style="width:${{d}}px;height:${{d}}px;background:${{o.c}};font-size:${{gross?12:11}}px">${{o.no}}</div>`}})}}).addTo(map);
  const pr=o.preis?(o.preis.toLocaleString("de-DE",{{minimumFractionDigits:2,maximumFractionDigits:2}})+" €"
      +(o.gepr?" <b>geprüft</b>":" <i>Anzeigepreis</i>")+(o.ppn?` · ${{Math.round(o.ppn)}} €/Pers./Nacht`:"")):"Preis offen";
  m.bindPopup(`<b>${{o.no}}. ${{o.name}}</b><br>${{o.typ||""}} · ${{o.st}}<br>${{pr}}`
    +(o.gesch?"<br><i>Lage geschätzt</i>":"")
    +`<br><a href="#obj${{o.no}}">Zum Katalogeintrag</a>`);
  idx[o.no]=m;
}});
const B=L.latLngBounds(D.filter(o=>o.st!=="Ausweichregion").map(o=>[o.lat,o.lon]));
map.fitBounds(B,{{padding:[45,45]}});
const sd=document.getElementById("stil");
sd.innerHTML="<span style='color:#6f675b'>Kartenstil:</span>"+Object.keys(K).map((k,i)=>
  `<label><input type="radio" name="b" ${{i===0?"checked":""}} value="${{k}}">${{k}}</label>`).join("")
 +`<label><input type="checkbox" id="alle">Ausweichregion einblenden</label>`;
sd.addEventListener("change",e=>{{
  if(e.target.name==="b"){{Object.values(K).forEach(l=>map.removeLayer(l));K[e.target.value].addTo(map);}}
  if(e.target.id==="alle"){{map.fitBounds(e.target.checked
      ? L.latLngBounds(D.map(o=>[o.lat,o.lon])) : B,{{padding:[45,45]}});}}
}});
document.getElementById("legende").innerHTML=LEG.map(l=>
  `<span><i style="background:${{l.c}}"></i>${{l.l}}</span>`).join("")
  +`<span style="margin-left:6px"><i style="background:#fff;border:2px dashed #6f675b"></i>Lage geschätzt</span>`;
document.querySelectorAll(".zeig").forEach(b=>b.addEventListener("click",()=>{{
  const m=idx[+b.dataset.no]; if(!m) return;
  document.getElementById("mapwrap").scrollIntoView({{behavior:"smooth",block:"center"}});
  map.setView(m.getLatLng(),16); m.openPopup();
}}));
document.getElementById("druck").addEventListener("click",()=>{{
  const b=document.getElementById("druck"); b.textContent="Kacheln werden geladen…";
  map.invalidateSize();
  setTimeout(()=>{{b.textContent="Als PDF drucken";window.print();}},2500);
}});
window.__bereit=true;
</script></body></html>"""
out=os.path.join(BASE,"Reisefuehrer-Turracher-Hoehe.html")
open(out,"w",encoding="utf-8").write(HTML)
print(f"Reiseführer: {len(HTML)/1024:.0f} KB, {len([o for o in SORT if o.get('lat')])} Marker, {len(sektionen)} Abschnitte")
