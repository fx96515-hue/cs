import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const [,, file, out, w, h] = process.argv;
const b = await chromium.launch({ args: ['--allow-file-access-from-files','--no-sandbox'] });
const p = await b.newPage({ viewport: { width: +w||1300, height: +h||1200 } });
const errs = [];
p.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));
p.on('console', m => { if (m.type() === 'error') errs.push('CONSOLE: ' + m.text().slice(0,160)); });
await p.goto('file://' + file, { waitUntil: 'load' });
try {
  await p.waitForFunction(() => document.title.startsWith('READY'), { timeout: 90000 });
  console.log('render fertig:', await p.title());
} catch (e) { console.log('TIMEOUT beim Rendern — Titel:', await p.title()); }
await p.screenshot({ path: out, fullPage: true });
if (errs.length) console.log(errs.slice(0,6).join('\n'));
await b.close();
