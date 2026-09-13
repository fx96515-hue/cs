import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const b=await chromium.launch({args:['--no-sandbox','--allow-file-access-from-files']});
const p=await b.newPage({viewport:{width:1200,height:1000}});
const err=[];
p.on('pageerror',e=>err.push('JS: '+e.message));
p.on('console',m=>{if(m.type()==='error'&&!/tile|net::ERR|Failed to load resource/i.test(m.text()))err.push('KONS: '+m.text().slice(0,130));});
await p.goto('file://'+process.cwd()+'/Reisefuehrer-Turracher-Hoehe.html');
await p.waitForFunction(()=>window.__bereit===true,{timeout:25000});
const r={};
r.marker=await p.locator('.mark').count();
r.gestrichelt=await p.locator('.mark.gesch').count();
r.katalogkarten=await p.locator('article.karte').count();
r.abschnitte=await p.locator('section.sek').count();
r.kartenstile=await p.locator('[name="b"]').count();
r.legende=await p.locator('#legende span').count();
r.zeigKnoepfe=await p.locator('.zeig').count();
r.kachelImgs=await p.evaluate(()=>document.querySelectorAll('img.leaflet-tile').length);
r.attribution=(await p.locator('.leaflet-control-attribution').innerText()).slice(0,70);
// Sprung von Karte zu Katalogeintrag
await p.locator('.mark').first().click({force:true});
await p.waitForSelector('.leaflet-popup-content',{timeout:6000});
r.popup=(await p.locator('.leaflet-popup-content').innerText()).split('\n')[0].slice(0,52);
r.popupAnker=await p.locator('.leaflet-popup-content a[href^="#obj"]').count();
// "Auf der Karte zeigen"
await p.locator('.zeig').first().click();
await p.waitForTimeout(700);
r.nachZeigen=await p.locator('.leaflet-popup-content').count();
// Druckansicht pruefen
await p.emulateMedia({media:'print'});
r.druckKarteSichtbar=await p.locator('#map').isVisible();
r.druckKnopfVersteckt=!(await p.locator('#druck').isVisible());
r.druckKartenHoehe=await p.locator('#map').evaluate(e=>e.getBoundingClientRect().height);
await p.emulateMedia({media:'screen'});
await p.screenshot({path:'_rf.png'});
console.log(JSON.stringify(r,null,1));
console.log(err.length?'PROBLEME:\n'+err.slice(0,5).join('\n'):'keine JS-Fehler');
await b.close();
