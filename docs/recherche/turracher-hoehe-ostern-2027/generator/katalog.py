# -*- coding: utf-8 -*-
import json, math, html, os

BASE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(BASE, "objekte.json"), encoding="utf-8"))
META, OBJ = D["meta"], D["objekte"]
SURF = "#fcfcfb"

# Ordinale Eignungs-Rampe (validiert: monoton, Delta-L, Hellende 2,44:1, ein Farbton)
RANK = {"ok": 0, "grenzwertig": 1, "anfrage": 2, "neu": 2, "unklar": 2, "belegt": 3,
        "zwei": 3, "ko": 4, "fallback": 2}
RAMP = ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec"]
LABEL = {
    "ok":          "Erfüllt alle Kernkriterien",
    "grenzwertig": "Grenzfall",
    "neu":         "Nur über Kartensuche, Belegung offen",
    "unklar":      "Belegung unverifiziert",
    "zwei":        "Zwei Einheiten nötig",
    "ko":          "Kriterium verfehlt",
    "fallback":    "Ausweichregion",
    "anfrage":     "Nur auf Anfrage",
    "belegt":      "Im Zeitraum belegt",
}
ORDER = ["ok", "grenzwertig", "anfrage", "neu", "unklar", "belegt", "zwei", "ko", "fallback"]
col   = lambda o: RAMP[RANK[o["status"]]]

def lum(hx):
    c = [int(hx[i:i+2], 16)/255 for i in (1, 3, 5)]
    c = [(v/12.92 if v <= .03928 else ((v+.055)/1.055)**2.4) for v in c]
    return .2126*c[0] + .7152*c[1] + .0722*c[2]
def ink(hx):   # Zahl im Marker: automatisch heller oder dunkler Text
    L = lum(hx)
    return "#ffffff" if (1.05/(L+.05)) >= (L+.05)/.05 else "#0b1c33"

def eur(v):  return "—" if v is None else f"{v:,.0f} €".replace(",", ".")
def eur2(v): return "—" if v is None else f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
def ppn(v, n=7, p=8): return "—" if v is None else f"{v/n/p:,.0f} €".replace(",", ".")
def esc(s):  return html.escape(str(s)) if s is not None else ""
def num(v):  return str(v).replace(".", ",")

def maps_link(o):
    if o.get("lat"): return f"https://www.google.com/maps/search/?api=1&query={o['lat']},{o['lon']}"
    q = (o["name"] + " " + o.get("ort", "")).replace(" ", "+")
    return f"https://www.google.com/maps/search/?api=1&query={q}"

CENTER = (46.9225, 13.8700)
def hav(a, b, c, d):
    R = 6371.0; p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c-a), math.radians(d-b)
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

PTS = [o for o in OBJ if o.get("lat") and o["zone"] in (1, 2)]
for o in OBJ:
    if o.get("lat"): o["_d"] = hav(CENTER[0], CENTER[1], o["lat"], o["lon"])

LA = [o["lat"] for o in PTS]; LO = [o["lon"] for o in PTS]
LA0, LA1, LO0, LO1 = min(LA), max(LA), min(LO), max(LO)
MLA = (LA0+LA1)/2
KX = 111.320*math.cos(math.radians(MLA)); KY = 110.574

def mk_proj(w, h, pad):
    sx = max((LO1-LO0)*KX, .2)*1.10; sy = max((LA1-LA0)*KY, .2)*1.10
    sc = min((w-2*pad)/sx, (h-2*pad)/sy)
    cx, cy = (LO0+LO1)/2, MLA
    return (lambda la, lo: (w/2 + (lo-cx)*KX*sc, h/2 - (la-cy)*KY*sc)), sc

# ---------- Übersichtskarte ----------
def overview(target_h=830, pad=30):
    # Satzspiegel A4 bei 14/12 mm Rand: 703 x 1024 px. Nach Abzug von Titel, Vorspann,
    # Legende und Bildunterschrift bleiben rund 830 px Hoehe fuer die Karte.
    sx = max((LO1-LO0)*KX, .2)*1.10; sy = max((LA1-LA0)*KY, .2)*1.10
    sc = (target_h - 2*pad)/sy                  # Massstab aus der Hoehe
    w = int(round(sx*sc + 2*pad)); h = target_h  # Breite folgt der Datenausdehnung
    cx, cy = (LO0+LO1)/2, MLA
    proj = lambda la, lo: (w/2 + (lo-cx)*KX*sc, h/2 - (la-cy)*KY*sc)
    s = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" class="map">',
         f'<rect width="{w}" height="{h}" fill="{SURF}" stroke="#ded8cd"/>', '<g stroke="#eeeae2" stroke-width="1">']
    la = math.floor(LA0*200)/200
    while la <= LA1+.005:
        y = proj(la, LO0)[1]
        if 6 < y < h-6: s.append(f'<line x1="6" y1="{y:.1f}" x2="{w-6}" y2="{y:.1f}"/>')
        la += .005
    lo = math.floor(LO0*200)/200
    while lo <= LO1+.005:
        x = proj(LA0, lo)[0]
        if 6 < x < w-6: s.append(f'<line x1="{x:.1f}" y1="6" x2="{x:.1f}" y2="{h-6}"/>')
        lo += .005
    s.append('</g>')
    ox, oy = proj(*CENTER)
    s.append(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="6" fill="none" stroke="#a8a293" stroke-width="1.2" stroke-dasharray="3 2"/>')
    s.append(f'<text x="{ox-9:.1f}" y="{oy-8:.1f}" font-size="9" fill="#847c6d" font-style="italic" text-anchor="end">Ortsmitte</text>')

    nodes = []; n = 0
    for st in ORDER:
        for o in [p for p in PTS if p["status"] == st]:
            n += 1; o["_no"] = n
            tx, ty = proj(o["lat"], o["lon"])
            nodes.append({"o": o, "tx": tx, "ty": ty, "x": tx, "y": ty, "n": n})
    R, SEP = 10.0, 21.5
    for _ in range(420):
        mv = False
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                a, b = nodes[i], nodes[j]
                dx, dy = b["x"]-a["x"], b["y"]-a["y"]; d = math.hypot(dx, dy)
                if d < SEP:
                    if d < .01: dx, dy, d = .6, -.8, 1.
                    p = (SEP-d)/2.; ux, uy = dx/d, dy/d
                    a["x"] -= ux*p; a["y"] -= uy*p; b["x"] += ux*p; b["y"] += uy*p; mv = True
        for nd in nodes:
            nd["x"] += (nd["tx"]-nd["x"])*.06; nd["y"] += (nd["ty"]-nd["y"])*.06
            nd["x"] = min(max(nd["x"], R+4), w-R-4); nd["y"] = min(max(nd["y"], R+4), h-R-4)
        if not mv: break
    for nd in nodes:
        c = col(nd["o"])
        if math.hypot(nd["x"]-nd["tx"], nd["y"]-nd["ty"]) > 3.5:
            s.append(f'<line x1="{nd["tx"]:.1f}" y1="{nd["ty"]:.1f}" x2="{nd["x"]:.1f}" y2="{nd["y"]:.1f}" stroke="{c}" stroke-width=".9" stroke-opacity=".5"/>')
            s.append(f'<circle cx="{nd["tx"]:.1f}" cy="{nd["ty"]:.1f}" r="1.8" fill="{c}"/>')
    for nd in nodes:
        o = nd["o"]; c = col(o)
        dash = ' stroke-dasharray="2.6 2"' if o["status"] == "neu" else ''
        s.append(f'<circle cx="{nd["x"]:.1f}" cy="{nd["y"]:.1f}" r="{R}" fill="{c}" stroke="{SURF}" stroke-width="2"{dash}/>')
        s.append(f'<text x="{nd["x"]:.1f}" y="{nd["y"]+3.4:.1f}" font-size="9.4" font-weight="700" fill="{ink(c)}" text-anchor="middle">{nd["n"]}</text>')
    for km in (2, 1, .5, .25):
        px = km*sc
        if px < (w-2*pad)*.60: break
    bx, by = 20, h-22
    s.append(f'<line x1="{bx}" y1="{by}" x2="{bx+px:.1f}" y2="{by}" stroke="#4a4438" stroke-width="2"/>')
    s.append(f'<line x1="{bx}" y1="{by-4}" x2="{bx}" y2="{by+4}" stroke="#4a4438" stroke-width="2"/>')
    s.append(f'<line x1="{bx+px:.1f}" y1="{by-4}" x2="{bx+px:.1f}" y2="{by+4}" stroke="#4a4438" stroke-width="2"/>')
    s.append(f'<text x="{bx+px/2:.1f}" y="{by-8:.1f}" font-size="9.5" fill="#4a4438" text-anchor="middle">{num(f"{km:g}")} km</text>')
    nx, ny = w-26, 28
    s.append(f'<path d="M {nx} {ny-13} L {nx+5} {ny+7} L {nx} {ny+2.5} L {nx-5} {ny+7} Z" fill="#4a4438"/>')
    s.append(f'<text x="{nx}" y="{ny+19}" font-size="9" fill="#4a4438" text-anchor="middle">N</text></svg>')
    return "\n".join(s), [nd["o"] for nd in nodes], w, h

MAP_SVG, MAPPED, MAPW, MAPH = overview()

# ---------- Mini-Lagekarte je Katalogeintrag ----------
def mini(o, w=132, h=96, pad=11):
    proj, sc = mk_proj(w, h, pad)
    s = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" class="mini">',
         f'<rect width="{w}" height="{h}" fill="{SURF}" stroke="#e4ded3"/>']
    ox, oy = proj(*CENTER)
    s.append(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="3" fill="none" stroke="#bdb7a8" stroke-width=".9" stroke-dasharray="2 1.6"/>')
    for p in PTS:
        if p is o: continue
        x, y = proj(p["lat"], p["lon"])
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.7" fill="#cfcabd"/>')
    if o.get("lat"):
        x, y = proj(o["lat"], o["lon"]); c = col(o)
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8.5" fill="none" stroke="{c}" stroke-width="1.1" stroke-opacity=".45"/>')
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.4" fill="{c}" stroke="{SURF}" stroke-width="1.4"/>')
        cap = f'{o["_d"]:.1f} km zur Ortsmitte'.replace(".", ",")
    else:
        s.append(f'<text x="{w/2}" y="{h/2+3}" font-size="8" fill="#8a8275" text-anchor="middle">keine Koordinaten</text>')
        cap = "Lage laut Adresse"
    s.append(f'<text x="{w/2}" y="{h-4}" font-size="7.2" fill="#847c6d" text-anchor="middle">{cap}</text></svg>')
    return "\n".join(s)

# ---------- Preisverteilung nach Eignung ----------
def strip(w=690, h=430):
    rows = [st for st in ORDER if st != "fallback" and any(o["status"] == st and o.get("p7") for o in OBJ)]
    L, R, T = 178, 24, 20
    rh = (h-T-30)/len(rows)
    vals = [o["p7"] for o in OBJ if o.get("p7") and o["status"] != "fallback"]
    lo, hi = min(vals)*.96, max(vals)*1.04
    X = lambda v: L + (v-lo)/(hi-lo)*(w-L-R)
    s = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" class="chart">',
         f'<rect width="{w}" height="{h}" fill="{SURF}"/>']
    for gv in range(3000, 7501, 1000):
        if lo <= gv <= hi:
            x = X(gv)
            s.append(f'<line x1="{x:.1f}" y1="{T}" x2="{x:.1f}" y2="{h-30:.1f}" stroke="#e8e3da" stroke-width="1"/>')
            s.append(f'<text x="{x:.1f}" y="{h-16:.1f}" font-size="8.4" fill="#6e675c" text-anchor="middle">{eur(gv)}</text>')
    s.append(f'<text x="{L}" y="{h-4:.1f}" font-size="8" fill="#8a8275">Gesamtpreis für 7 Nächte, ganze Gruppe</text>')
    for i, st in enumerate(rows):
        cy = T + rh*i + rh/2
        s.append(f'<text x="{L-10}" y="{cy-2:.1f}" font-size="8.6" fill="#2b2820" text-anchor="end">{LABEL[st]}</text>')
        grp = sorted([o for o in OBJ if o["status"] == st and o.get("p7")], key=lambda z: z["p7"])
        s.append(f'<text x="{L-10}" y="{cy+8:.1f}" font-size="7.4" fill="#8a8275" text-anchor="end">{len(grp)} Objekte</text>')
        s.append(f'<line x1="{L}" y1="{cy:.1f}" x2="{w-R}" y2="{cy:.1f}" stroke="#f0ece4" stroke-width="1"/>')
        c = RAMP[RANK[st]]
        seen = []
        for o in grp:
            x = X(o["p7"]); dy = 0
            while any(abs(x-sx) < 9 and abs(dy-sd) < 8 for sx, sd in seen): dy += 8.5
            seen.append((x, dy))
            s.append(f'<circle cx="{x:.1f}" cy="{cy-dy:.1f}" r="4.6" fill="{c}" stroke="{SURF}" stroke-width="2"/>')
        if grp:
            s.append(f'<text x="{X(grp[0]["p7"]):.1f}" y="{cy+13:.1f}" font-size="7.2" fill="#4a4438" text-anchor="middle">{eur(grp[0]["p7"])}</text>')
    s.append('</svg>')
    return "\n".join(s)

CHART = strip()
PY = [o["p7"] for o in OBJ if o.get("p7") and o["zone"] == 1]

CSS = """
@page { size:A4; margin:14mm 12mm 12mm; }
@page:first { margin:0; }
*{box-sizing:border-box}
body{font-family:"DejaVu Serif",Georgia,serif;color:#23201b;font-size:9.4pt;line-height:1.5;margin:0}
h1,h2,h3,h4,.sans{font-family:"DejaVu Sans",Helvetica,Arial,sans-serif}
h1{font-size:30pt;letter-spacing:-.6pt;line-height:1.06;margin:0 0 .2em;color:#0d1a2b}
h2{font-size:14.5pt;margin:0 0 .5em;padding-bottom:5px;border-bottom:2.5px solid #0d366b;color:#0d1a2b}
h3{font-size:10.6pt;margin:0}
a{color:#184f95;text-decoration:none;border-bottom:.5px solid #bcd0e6}
.page{page-break-after:always}.page:last-child{page-break-after:auto}

.cover{height:297mm;padding:26mm 22mm;display:flex;flex-direction:column;justify-content:space-between;
       background:#0d366b;color:#eef3f9}
.cover h1{color:#fff}
.cover .eyebrow{font-size:8.6pt;letter-spacing:3pt;text-transform:uppercase;color:#9dc0e8}
.cover .rule{height:3px;width:78px;background:#6da7ec;margin:15px 0 20px}
.cover .sub{font-size:12pt;color:#c3d7ef;font-style:italic;margin-top:.5em}
.cfacts{display:grid;grid-template-columns:1fr 1fr;gap:0}
.cfacts{border-top:1px solid #2d5688}
.cfacts div{border-bottom:1px solid #1b4577;padding:8px 14px 8px 0}
.cfacts .k{font-family:"DejaVu Sans",sans-serif;font-size:7.2pt;letter-spacing:1.2pt;text-transform:uppercase;color:#8fb4de}
.cfacts .v{font-size:10.4pt;color:#fff}
.cstamp{font-size:8pt;color:#9dc0e8;border-top:1px solid #2d5688;padding-top:9px}

.lead{font-size:11pt;line-height:1.55;color:#33302a;margin:0 0 1em}
.kbox{background:#f2f6fb;border-left:3.5px solid #0d366b;padding:11px 14px;margin:13px 0}
.kbox h4{font-size:8.2pt;letter-spacing:1.3pt;text-transform:uppercase;color:#0d366b;margin:0 0 .4em}
.kbox p{margin:0}
.warn{background:#faf6f0;border-left-color:#8a6a3b}.warn h4{color:#8a6a3b}

.map{display:block;flex:none}
.mapwrap{display:flex;gap:15px;align-items:flex-start;margin-top:8px;break-inside:avoid}
.mapcol{flex:0 0 auto}
.maplg{flex:1;column-count:2;column-gap:11px;font-size:7.4pt}
.lg{break-inside:avoid;display:flex;gap:5px;margin-bottom:2.4px}
.lgn{line-height:1.26}
.no{display:inline-block;min-width:14px;height:14px;border-radius:7px;font-family:"DejaVu Sans",sans-serif;
    font-size:7.4pt;font-weight:700;text-align:center;line-height:14px;padding:0 3px;flex:none}
.rank{margin:8px 0 3px;font-family:"DejaVu Sans",sans-serif;font-size:7.6pt}
.rank span{display:inline-block;margin-right:12px;white-space:nowrap}
.rank i{display:inline-block;width:10px;height:10px;border-radius:5px;margin-right:4px;vertical-align:-1px}
.chart{display:block;width:690px;height:430px;margin-top:8px}

.entry{border:1px solid #e2ddd3;border-radius:3px;padding:11px 13px 9px;margin-bottom:10px;break-inside:avoid}
.ehead{display:flex;align-items:baseline;gap:8px;margin-bottom:8px}
.ehead h3{flex:1;color:#0d1a2b}
.badge{font-family:"DejaVu Sans",sans-serif;font-size:7.2pt;padding:2px 7px;border-radius:9px;color:#fff;white-space:nowrap}
.ebody{display:flex;gap:13px;align-items:flex-start}
.mini{flex:none;width:132px;height:96px;display:block;border-radius:2px}
.ekv{flex:1}
table.kv{width:100%;border-collapse:collapse;font-size:8.5pt}
table.kv th{text-align:left;font-family:"DejaVu Sans",sans-serif;font-weight:400;color:#8a8275;
            width:31%;padding:2.2px 8px 2.2px 0;vertical-align:top;font-size:7.9pt}
table.kv td{padding:2.2px 0;vertical-align:top}
.note{font-size:8.6pt;color:#464037;margin:7px 0 5px}
.links{font-size:8pt;margin:0}
.price{font-size:11pt;font-weight:700;color:#0d366b;font-family:"DejaVu Sans",sans-serif}

table.lst{width:100%;border-collapse:collapse;font-size:7.8pt;margin-top:6px}
table.lst thead th{font-family:"DejaVu Sans",sans-serif;font-size:7pt;letter-spacing:.4pt;text-transform:uppercase;
                   color:#6f675b;text-align:left;border-bottom:1.5px solid #23201b;padding:4px 5px 4px 0}
table.lst td{padding:3.2px 5px 3.2px 0;border-bottom:.5px solid #eeeae2;vertical-align:top}
table.lst td.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
table.lst td.src{color:#8a8275;font-size:7.1pt}
tr.grp td{background:#f2f6fb;font-family:"DejaVu Sans",sans-serif;font-size:7.3pt;letter-spacing:1pt;
          text-transform:uppercase;color:#0d366b;padding:5px 0 4px;border-bottom:1px solid #d3e0ef}
ul{margin:.3em 0 .8em;padding-left:1.1em}li{margin-bottom:.3em}
.small{font-size:8pt;color:#5a5449}
.foot{font-size:7.5pt;color:#8a8275;border-top:1px solid #ded7cc;padding-top:7px;margin-top:12px}
.secthead{font-family:"DejaVu Sans",sans-serif;font-size:7.6pt;letter-spacing:1.6pt;text-transform:uppercase;
          color:#0d366b;margin:0 0 7px}
"""

def entry(o):
    c = col(o); rows = []
    def r(k, v):
        if v not in (None, "", "—"): rows.append(f"<tr><th>{k}</th><td>{v}</td></tr>")
    adr = " ".join(x for x in [o.get("adresse",""), o.get("plz",""), o.get("ort","")] if x)
    r("Typ", esc(o["typ"]));  r("Adresse", esc(adr))
    if o.get("max"):
        r("Belegung", f"max. {o['max']} Personen"
          + (f" &middot; {o['sz']} Schlafzimmer" if o.get("sz") else "")
          + (f" &middot; {o['bad']} Bäder" if o.get("bad") else ""))
    n = o.get("naechte", 7)
    if o.get("gesamt"):
        r("<b>Gesamtkosten geprüft</b>",
          f"<span class='price'>{eur2(o['gesamt'])}</span> für {n} Nächte"
          f" &middot; {o['ppn']:.0f} € je Person und Nacht")
        if o.get("p7") and abs(o["p7"] - o["gesamt"]) > 1:
            diff = o["gesamt"] - o["p7"]
            wie = (f"{eur2(diff)} Nebenkosten kommen hinzu" if diff > 0
                   else f"{eur2(-diff)} günstiger als der Anzeigepreis, anderer Buchungskanal")
            r("Anzeigepreis Portal", f"{eur2(o['p7'])} &middot; {wie}")
    elif o.get("p7"):
        r("7 Nächte (Anzeigepreis)", f"<span class='price'>{eur2(o['p7'])}</span> &middot; {ppn(o['p7'],7)} je Person und Nacht")
    if o.get("p5") and not o.get("gesamt"): r("5 Nächte", f"{eur2(o['p5'])} &middot; {ppn(o['p5'],5)} je Person und Nacht")
    if o.get("nebenkosten"): r("Nebenkosten", esc(o["nebenkosten"])[:150])
    if o.get("storno"): r("Storno", esc(o["storno"])[:115])
    if o.get("verfuegbar"): r("Verfügbarkeit", esc(o["verfuegbar"])[:105])
    if o.get("sz_text") and not o.get("sz"): r("Schlafzimmer", esc(o["sz_text"])[:95])
    if o.get("bad_text") and not o.get("bad"): r("Bäder", esc(o["bad_text"])[:95])
    if o.get("kanal"): r("Buchungskanal", esc(o["kanal"]))
    if o.get("kaution"): r("Kaution", eur(o["kaution"]))
    if o.get("taxe"): r("Ortstaxe", esc(o["taxe"]))
    if o.get("rating"): r("Bewertung", f"{num(o['rating'])} aus {o['reviews']} Rezensionen, {esc(o['quelle'])}")
    if o.get("google"): r("Google", esc(o["google"]))
    if o.get("tel"): r("Telefon", esc(o["tel"]))
    if o.get("lat"): r("Koordinaten", f"{o['lat']:.5f}, {o['lon']:.5f}")
    lk = [f'<a href="{esc(o["url"])}">Angebot mit Fotos</a>']
    if o.get("direkt"): lk.append(f'<a href="{esc(o["direkt"])}">Direkt beim Anbieter</a>')
    lk.append(f'<a href="{maps_link(o)}">In Google Maps öffnen</a>')
    no = (f'<span class="no" style="background:{c};color:{ink(c)}">{o["_no"]}</span>' if o.get("_no") else "")
    return f"""<div class="entry">
 <div class="ehead">{no}<h3>{esc(o['name'])}</h3><span class="badge" style="background:{c}">{LABEL[o['status']]}</span></div>
 <div class="ebody">{mini(o)}<div class="ekv"><table class="kv">{''.join(rows)}</table></div></div>
 <p class="note">{esc(o.get('hinweis',''))}</p>
 {f'<p class="note" style="color:#7a5a2a"><b>Schwachpunkt:</b> {esc(o["schwaeche"])[:190]}</p>' if o.get("schwaeche") else ""}
 <p class="links">{' &nbsp;·&nbsp; '.join(lk)}</p>
</div>"""

def rowsof(objs, dist=False):
    out = []
    for o in objs:
        rat = (f"{num(o['rating'])} ({o['reviews']})" if o.get("rating") else (o.get("google") or "—"))
        d = (f"{o['_d']:.1f} km".replace(".", ",") if o.get("_d") else "—")
        preis = o.get("gesamt") or o.get("p7")
        marke = " ●" if o.get("gesamt") else ""
        out.append(f"<tr><td><a href='{esc(o['url'])}'>{esc(o['name'])}</a></td><td>{esc(o['typ'])}</td>"
                   f"<td>{esc(o['ort'])}</td><td>{o.get('max') or '—'}</td>"
                   f"<td>{(str(o['sz'])+'/'+str(o['bad'])) if o.get('sz') and o.get('bad') else '—'}</td>"
                   + (f"<td class='num'>{d}</td>" if dist else "")
                   + f"<td class='num'>{eur(preis)}{marke}</td>"
                     f"<td class='num'>{(('%.0f €' % o['ppn']) if o.get('ppn') else ppn(o.get('p7'),7))}</td>"
                     f"<td>{rat}</td><td class='src'>{esc(o['quelle'])}</td></tr>")
    return "".join(out)

by  = lambda st: [o for o in OBJ if o["status"] == st]
top = sorted(by("ok"), key=lambda o: o.get("gesamt") or o.get("p7") or 9e9)
top7 = [o for o in top if o.get("gesamt") and o.get("naechte", 7) == 7]
GEPRUEFT = [o for o in OBJ if o.get("gesamt")]

def median(v):
    v = sorted(v); n = len(v)
    return v[n//2] if n % 2 else (v[n//2-1]+v[n//2])/2

def stats_table():
    rows = []
    for st in ORDER:
        if st == "fallback": continue
        g = [o["p7"] for o in OBJ if o["status"] == st and o.get("p7")]
        n_all = len(by(st))
        if not g:
            rows.append(f"<tr><td>{LABEL[st]}</td><td class='num'>{n_all}</td>"
                        "<td class='num'>—</td><td class='num'>—</td>"
                        "<td class='num'>—</td><td class='num'>—</td></tr>")
        else:
            rows.append(f"<tr><td>{LABEL[st]}</td><td class='num'>{n_all}</td>"
                        f"<td class='num'>{eur(min(g))}</td><td class='num'>{eur(median(g))}</td>"
                        f"<td class='num'>{eur(max(g))}</td>"
                        f"<td class='num'>{ppn(median(g),7)}</td></tr>")
    return ("<table class='lst'><thead><tr><th>Gruppe</th><th>Objekte</th><th>Günstigster</th>"
            "<th>Median</th><th>Teuerster</th><th>Median je Person/Nacht</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>")

STATS = stats_table()
P = []

P.append(f"""<div class="page cover">
 <div><div class="eyebrow">Unterkunfts-Katalog</div><div class="rule"></div>
  <h1>Turracher Höhe<br>Osterferien 2027</h1>
  <div class="sub">{len(OBJ)} Objekte für 8 Personen &middot; Anreise 20. März 2027</div></div>
 <div><div class="cfacts">
   <div><div class="k">Anreise</div><div class="v">{META['anreise']}</div></div>
   <div><div class="k">Abreise</div><div class="v">{META['abreise_haupt']}</div></div>
   <div><div class="k">Aufenthalt</div><div class="v">7 Nächte, ab 5 möglich</div></div>
   <div><div class="k">Belegung</div><div class="v">5 Erwachsene + {META['kinder']}</div></div>
   <div><div class="k">Schulferien</div><div class="v">{META['ferien']}</div></div>
   <div><div class="k">Kalenderlage</div><div class="v">Karwoche, Karfreitag {META['karfreitag']}</div></div>
   <div><div class="k">Preisspanne im Ort</div><div class="v">{eur(min(PY))} – {eur(max(PY))}</div></div>
   <div><div class="k">Zielgebiet</div><div class="v">1.763 m, Kärnten / Steiermark</div></div>
  </div>
  <p class="cstamp">Datenstand 13.09.2026 &middot; alle Preise in Euro für die gesamte Gruppe &middot;
  Quellen: Booking.com, Trivago, Kartensuche, Websuche</p></div>
</div>""")

lgnd = "".join(f'<div class="lg"><span class="no" style="background:{col(o)};color:{ink(col(o))}">{o["_no"]}</span>'
               f'<span class="lgn">{esc(o["name"])}</span></div>' for o in MAPPED)
rankleg = "".join(f'<span><i style="background:{RAMP[RANK[st]]}"></i>{LABEL[st]}</span>'
                  for st in ["ok","grenzwertig","unklar","zwei","ko"])

P.append(f"""<div class="page">
 <h2>Das Wichtigste zuerst</h2>
 <p class="lead">Erfasst sind <b>{len(OBJ)} Objekte</b>. Bei <b>{len(GEPRUEFT)}</b> davon wurde die
 Verfügbarkeit für den Zeitraum einzeln abgefragt und die <b>Gesamtkosten inklusive aller Nebenkosten</b>
 durchgerechnet — das ist der Unterschied zwischen Anzeigepreis und dem, was am Ende zu zahlen ist.
 <b>{len(top7)} Objekte</b> sind frei und erfüllen alle acht Kernkriterien.</p>
 <div class="kbox"><h4>Empfehlung</h4>
  <p><b>{esc(top7[0]["name"].split("(")[0].strip())}</b> mit <b>{eur2(top7[0]["gesamt"])}</b> Gesamtkosten
  ({top7[0]["ppn"]:.0f} € je Person und Nacht). Es ist das günstigste Objekt, das alle acht Kernkriterien erfüllt
  und im Zeitraum frei ist: vier Schlafzimmer, zwei Bäder, Carport für zwei Autos, Skiraum mit beheiztem
  Schuhtrockner. Entscheidend ist eine Besonderheit der Abrechnung — <b>die Endreinigung von 222 € schließt Strom,
  Wasser und Brennholz ein</b>, es gibt also kein Nachzahlungsrisiko. Kostenfreie Stornierung bis 18.02.2027.</p>
  <p style="margin-top:7px">Der Nachteil: exakt acht Schlafplätze ohne jede Reserve, Zustellbetten sind
  ausgeschlossen.</p></div>
 <h3 style="margin:14px 0 5px">Fünf Befunde, die die Entscheidung verschieben</h3>
 <ul>
  <li><b>Der Anzeigepreis ist nicht der Preis.</b> Erst die Einzelprüfung zeigt die Gesamtkosten. Beim
      Appartementhaus Lerchbaumer kommen zu 2.030 € Grundmiete 260 € Endreinigung und 122,50 € Ortstaxe —
      und die drei Kinder sind von der Taxe befreit, weil sie erst ab 15 Jahren anfällt.</li>
  <li><b>Direktbuchung spart bis zu 19 %.</b> Bei ALPS RESORTS liegt die Ersparnis gegenüber dem Portal
      bei 748 € (Alpenpark) und 782 € (Superior Chalet 25). Bei Ibex und Hollmann ist es umgekehrt: dort
      ist das Portal günstiger. Pauschal gilt keine der beiden Richtungen.</li>
  <li><b>Bäder sind der Engpass, nicht Betten.</b> Das mit Abstand günstigste Objekt — die Zirbenhütte für
      2.412,50 €, also 43 € je Person und Nacht — hat vier Schlafzimmer, aber nur <b>ein</b> Bad für acht
      Personen. Es scheitert an genau diesem einen Kriterium.</li>
  <li><b>Fünf Nächte sind nicht billiger.</b> Turrach Lodges kostet für fünf Nächte 3.006 €, das sind
      75 € je Person und Nacht — mehr als jedes der zehn vollständig geeigneten Sieben-Nächte-Angebote.
      Für acht Personen sind dort sieben Nächte gar nicht verfügbar.</li>
  <li><b>Das offizielle Ortsverzeichnis ist vollständig erfasst</b> — 55 Betriebe — und die Siedlungssuche
      hat darüber hinaus Häuser gefunden, die auf keinem Portal stehen.</li>
 </ul>
 <div class="kbox warn"><h4>Belastbarkeit dieser Zahlen</h4>
  <p>Bei <b>{len(GEPRUEFT)} Objekten</b> sind die Gesamtkosten durchgerechnet und mit einem Punkt im Register
  markiert. Bei allen übrigen stehen <b>Portal-Anzeigepreise ohne Nebenkosten</b> — dort fehlen Endreinigung,
  Ortstaxe, Bettwäsche und Energie, was erfahrungsgemäß 250 bis 600 € ausmacht. Die Ortstaxe beträgt je nach
  Gemeinde 2,50 bis 3,50 € pro Erwachsenem und Nacht; Kinder sind teils befreit.
  Fotos ließen sich nicht einbetten: die Netzwerk-Policy dieser Umgebung sperrt sämtliche externen Bildhosts
  und Kartendienste. Jeder Objektname führt per Link direkt zur Anzeige mit Bildern.</p></div>
</div>""")

P.append(f"""<div class="page">
 <h2>Lage</h2>
 <p class="small">Maßstabsgetreu aus den Geokoordinaten gezeichnet, gleicher Maßstab in beide Richtungen,
 Gitternetz in Schritten von 0,005 Grad. Enthalten sind {len(MAPPED)} Objekte.
 Die Farbe zeigt die Eignung als Rangfolge: je dunkler, desto besser passt das Objekt auf acht Personen.
 <b>Gestrichelter Rand</b> heißt: nur über die Kartensuche gefunden, Belegung noch offen und Lage aus der
 Hausnummern-Nachbarschaft geschätzt, nicht verifiziert.</p>
 <div class="rank">{rankleg}</div>
 <div class="mapwrap"><div class="mapcol">{MAP_SVG}</div><div class="maplg">{lgnd}</div></div>
 <p class="small" style="margin-top:7px">Dicht beieinanderliegende Marker sind auseinandergerückt; die dünne Linie
 und der kleine Punkt zeigen den tatsächlichen Standort.</p>
</div>""")

P.append(f"""<div class="page">
 <h2>Was die Eignung kostet</h2>
 <p class="lead">Jeder Punkt ist ein Objekt, waagrecht aufgetragen nach Gesamtpreis für sieben Nächte.
 Die Zeilen sind nach Eignung sortiert. Das Ergebnis widerspricht der Erwartung: Die Objekte, die alle
 Kernkriterien erfüllen, sind <b>nicht teurer</b> — sie sind im Mittel sogar günstiger. Ihr Median liegt bei
 3.858 €, der Median der Gruppe mit unverifizierter Belegung bei 4.026 €. Wer auf Nummer sicher geht, zahlt
 also keinen Aufschlag, sondern spart im Mittel rund 170 €.</p>
 {CHART}
 <div class="kbox" style="margin-top:16px"><h4>Lesehilfe</h4>
  <p>Am linken Rand jeder Zeile steht der günstigste Preis der Gruppe. Die Zeile „Belegung unverifiziert“ ist mit
  Abstand die größte — hier steckt das meiste ungehobene Potenzial, aber auch das meiste Risiko: Diese Objekte
  können sich als zu klein erweisen, sobald man nachfragt.</p></div>
 <p class="secthead" style="margin-top:15px">Kennzahlen je Gruppe</p>
 {STATS}
 <p class="small" style="margin-top:5px">Median = mittlerer Preis der Gruppe. Alle Werte sind
 Portal-Anzeigepreise für sieben Nächte und die gesamte Gruppe, ohne Nebenkosten.</p>
</div>""")

# ---------------- Katalogteil ----------------
SECT = [
    ("ok",          "Erfüllt alle Kernkriterien",
     "Acht Personen in einer Einheit, mindestens vier Schlafzimmer, mindestens zwei Bäder, kompletter Zeitraum verfügbar. Nach Preis sortiert."),
    ("grenzwertig", "Grenzfall",
     "Nimmt acht Personen auf, verfehlt aber ein Kriterium knapp."),
    ("neu",         "Nur über die Kartensuche gefunden",
     "Diese Betriebe erscheinen auf keinem der abgefragten Buchungsportale. Belegung und Preise sind unbekannt, sie brauchen eine Direktanfrage — und sind genau deshalb in einer Ferienwoche oft noch frei."),
    ("unklar",      "Belegung unverifiziert",
     "Preis und Bewertung liegen vor, die zulässige Personenzahl und die Zimmeraufteilung aber nicht. Vor einer Buchung zwingend nachfragen."),
    ("zwei",        "Zwei Einheiten nötig",
     "Die größte Einzeleinheit fasst weniger als acht Personen. Machbar, aber die Gruppe wird geteilt."),
    ("anfrage",     "Nur auf Anfrage buchbar",
     "Kein öffentlicher Buchungskalender für den Zeitraum. Belegung und Ausstattung sind teils geprüft, die Verfügbarkeit muss telefonisch oder per E-Mail geklärt werden."),
    ("belegt",      "Im Zeitraum belegt",
     "Geprüft und für 20.–27.03.2027 nicht verfügbar. Dokumentiert, weil eine Direktanfrage bei Stornierungen lohnen kann."),
    ("ko",          "Kriterium verfehlt",
     "Vollständigkeitshalber dokumentiert, nicht empfohlen — mit Angabe des verfehlten Kriteriums."),
]
for st, title, intro in SECT:
    grp = sorted(by(st), key=lambda o: (o.get("ppn") or (o["p7"]/56 if o.get("p7") else 9e9)))
    if not grp: continue
    P.append(f'<div class="page"><h2>{title}</h2><p class="small">{intro}</p>'
             + "".join(entry(o) for o in grp) + '</div>')

# ---------------- Register ----------------
allobj = sorted(OBJ, key=lambda o: (RANK[o["status"]], o.get("p7") or 9e9))
reg = []
for st, title, _ in SECT:
    g = sorted(by(st), key=lambda o: o.get("gesamt") or o.get("p7") or 9e9)
    if g: reg.append(f'<tr class="grp"><td colspan="9">{title}</td></tr>' + rowsof(g))
P.append(f"""<div class="page">
 <h2>Register</h2>
 <p class="small">Alle Objekte im Ortsgebiet und Umfeld. Preise für 7 Nächte, gesamte Gruppe,
 Portal-Anzeigepreis ohne Nebenkosten. €/P/N = je Person und Nacht bei acht Personen.</p>
 <table class="lst"><thead><tr><th>Objekt</th><th>Typ</th><th>Ort</th><th>Bel.</th><th>SZ/Bad</th>
 <th>7 Nächte</th><th>€/P/N</th><th>Bewertung</th><th>Quelle</th></tr></thead>
 <tbody>{''.join(reg)}</tbody></table>
</div>""")

fb = sorted(by("fallback"), key=lambda o: o.get("gesamt") or o.get("p7") or 9e9)
P.append(f"""<div class="page">
 <h2>Ausweichregion</h2>
 <p class="lead">Wer auf die Pistenanbindung der Turracher Höhe verzichtet, zahlt deutlich weniger. Das günstigste
 Objekt der Recherche kostet {eur(1637)} für sieben Nächte — rund {eur(3780-1637)} unter der besten Empfehlung
 im Ort. Die Entfernung ist Luftlinie zur Ortsmitte; die Fahrzeit liegt wegen der Bergstraßen deutlich darüber
 und ist nicht verifiziert.</p>
 <table class="lst"><thead><tr><th>Objekt</th><th>Typ</th><th>Ort</th><th>Bel.</th><th>SZ/Bad</th>
 <th>Luftlinie</th><th>7 Nächte</th><th>€/P/N</th><th>Bewertung</th><th>Quelle</th></tr></thead>
 <tbody>{rowsof(fb, dist=True)}</tbody></table>

 <h2 style="margin-top:20px">Nächste Schritte</h2>
 <ul>
  <li><b>Sofort:</b> Bei den beiden Vier-Bäder-Lodges die Gesamtkosten inklusive Endreinigung, Ortstaxe und
      Energie erfragen und die Stornofrist schriftlich bestätigen lassen.</li>
  <li><b>Parallel:</b> Die fünf Karten-Funde telefonisch anfragen — sie sind über Portale nicht abgedeckt und
      daher für die Karwoche eine realistische Chance.</li>
  <li><b>Vor der Buchung:</b> Direktpreis gegen Portalpreis stellen. ALPS RESORTS und die Hüttendörfer haben
      einen eigenen Direktvertrieb.</li>
  <li><b>Offen:</b> Ob der Liftbetrieb am 27. März 2027 noch läuft. Das Saisonende entscheidet über die letzten
      Urlaubstage und ist für 2027 noch nicht veröffentlicht.</li>
 </ul>
 <div class="foot">
  <b>Methodik.</b> Abgefragt wurden Booking.com (Ortssuche, Radiussuche über 15 km, Varianten mit 5 und 7 Nächten,
  Detailabfrage zu Belegung und Nebenkosten), Trivago als Metasuche über Airbnb, FeWo-direkt, Expedia und weitere,
  sowie eine Orts- und Siedlungssuche über Kartendaten. Ergänzend liefen zwei Agenten-Workflows über
  Ortsverzeichnis, Chaletportale, Ferienhaus-Veranstalter, Bewertungsportale und Anbieter-Direktseiten.
  Belegungs- und Zimmerangaben stammen, wo vorhanden, aus der Detailabfrage und beziehen sich auf die größte
  Einzeleinheit des Objekts.<br>
  <b>Grenzen.</b> Expedia war über die eigene Schnittstelle nicht erreichbar, der Bestand kam über Trivago herein.
  Die Preisprognose liefert für März 2027 keine Daten. Kartenkacheln, Geodatendienste und Bildhosts sind in der
  Ausführungsumgebung gesperrt; die Karten sind daher aus den erhobenen Koordinaten selbst gezeichnet.
  Alle Preise sind Anzeigepreise vom 13.09.2026 und können sich ändern.<br>
  <b>Farbgebung.</b> Die Eignungsrampe ist eine einfarbige ordinale Skala, geprüft auf monotone Helligkeit,
  ausreichende Stufenabstände, Kontrast zum Hintergrund und Lesbarkeit bei Farbfehlsichtigkeit.
 </div>
</div>""")

doc = ("<!doctype html><html lang='de'><head><meta charset='utf-8'>"
       "<title>Turracher Höhe – Unterkunfts-Katalog Ostern 2027</title>"
       f"<style>{CSS}</style></head><body>{''.join(P)}</body></html>")
open(os.path.join(BASE, "katalog.html"), "w", encoding="utf-8").write(doc)
print("Katalog-HTML:", len(doc), "Zeichen,", len(P), "Seitenblöcke")
