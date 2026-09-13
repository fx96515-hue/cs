/**
 * Erzeugt aus dem Reiseführer ein PDF MIT sichtbarer OpenTopoMap-Karte.
 * Muss lokal laufen — in der Recherche-Umgebung sind Kartenkacheln gesperrt.
 *
 *   npm install playwright && npx playwright install chromium
 *   node pdf-mit-karte.mjs
 *
 * Ergebnis: Reisefuehrer-Turracher-Hoehe.pdf
 */
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const hier = dirname(fileURLToPath(import.meta.url));
const quelle = join(hier, 'Reisefuehrer-Turracher-Hoehe.html');
const ziel   = join(hier, 'Reisefuehrer-Turracher-Hoehe.pdf');

const browser = await chromium.launch();
const seite = await browser.newPage({ viewport: { width: 1240, height: 1750 } });

let kacheln = 0, fehler = 0;
seite.on('response', r => { if (/tile|\.png/.test(r.url())) (r.ok() ? kacheln++ : fehler++); });

console.log('Lade Reiseführer …');
await seite.goto('file://' + quelle, { waitUntil: 'load' });
await seite.waitForFunction(() => window.__bereit === true, { timeout: 30000 });

console.log('Warte auf Kartenkacheln …');
await seite.waitForTimeout(4000);
await seite.waitForFunction(() => {
  const t = [...document.querySelectorAll('img.leaflet-tile')];
  return t.length > 0 && t.every(i => i.complete);
}, { timeout: 45000 }).catch(() => console.log('  (Zeitlimit — es wird mit dem gedruckt, was geladen ist)'));
await seite.waitForTimeout(1500);

if (kacheln === 0) {
  console.log('\nACHTUNG: Keine einzige Kachel geladen. Ohne Internetzugang zu');
  console.log('tile.opentopomap.org bleibt die Karte grau. PDF wird trotzdem erzeugt.\n');
} else {
  console.log(`  ${kacheln} Kacheln geladen${fehler ? `, ${fehler} fehlgeschlagen` : ''}.`);
}

await seite.emulateMedia({ media: 'print' });
await seite.pdf({
  path: ziel, format: 'A4', printBackground: true,
  margin: { top: '14mm', bottom: '14mm', left: '12mm', right: '12mm' },
  displayHeaderFooter: true, headerTemplate: '<span></span>',
  footerTemplate: '<div style="width:100%;font-size:8px;color:#8a8275;text-align:center;font-family:sans-serif">'
    + 'Turracher Höhe — Osterferien 2027 · Seite <span class="pageNumber"></span> von <span class="totalPages"></span></div>',
});
console.log('Fertig: ' + ziel);
await browser.close();
