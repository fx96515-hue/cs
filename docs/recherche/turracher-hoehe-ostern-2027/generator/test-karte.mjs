import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const b = await chromium.launch({ args:['--no-sandbox','--allow-file-access-from-files'] });
const p = await b.newPage({ viewport:{width:1400,height:900} });
const fehler = [];
p.on('pageerror', e => fehler.push('JS-FEHLER: ' + e.message));
p.on('console', m => { if (m.type()==='error' && !/tile|net::ERR|Failed to load resource/i.test(m.text()))
  fehler.push('KONSOLE: ' + m.text().slice(0,120)); });
await p.goto('file://' + process.cwd() + '/Karte-Turracher-Hoehe-OSM.html');
await p.waitForFunction(() => window.__bereit === true, { timeout: 20000 });

const r = {};
r.marker         = await p.locator('.mark').count();
r.gestrichelt    = await p.locator('.mark.gesch').count();
r.gruppenfilter  = await p.locator('[data-g]').count();
r.kartenstile    = await p.locator('[data-b]').count();
r.massstab       = await p.locator('.leaflet-control-scale').count();
r.attribution    = (await p.locator('.leaflet-control-attribution').innerText()).slice(0,80);
r.kachelanfragen = await p.evaluate(() => document.querySelectorAll('img.leaflet-tile').length);

// Popup testen
await p.locator('.mark').first().click({force:true});
await p.waitForSelector('.leaflet-popup-content h3', { timeout: 5000 });
r.popupTitel = await p.locator('.leaflet-popup-content h3').innerText();
r.popupLinks = await p.locator('.leaflet-popup-content .lk a').count();

// Preisfilter testen
const vorher = await p.locator('.mark').count();
await p.locator('#preis').evaluate(el => { el.value = 3900; el.dispatchEvent(new Event('input')); });
await p.waitForTimeout(400);
r.nachPreisfilter = await p.locator('.mark').count();
r.filterWirkt = r.nachPreisfilter < vorher;

// Gruppenfilter testen
await p.locator('[data-g]').first().uncheck();
await p.waitForTimeout(400);
r.nachGruppenfilter = await p.locator('.mark').count();

await p.locator('#preis').evaluate(el => { el.value = 7400; el.dispatchEvent(new Event('input')); });
await p.locator('[data-g]').first().check();
await p.waitForTimeout(400);
await p.screenshot({ path:'_karte.png' });
console.log(JSON.stringify(r, null, 1));
console.log(fehler.length ? 'PROBLEME:\n' + fehler.join('\n') : 'keine JS-Fehler');
await b.close();
