// Capturas reales de Amoxcalli para las diapositivas, con Chrome sin interfaz (protocolo CDP).
//   1. bash scripts/amoxcalli.sh serve --port 8833     (y esperar a que termine «Preparando el análisis…»)
//   2. node presentations/capturas.mjs /tmp/capturas http://127.0.0.1:8833 [pasos,separados,por,comas]
//   3. convertir a JPEG las que usan las diapositivas, p. ej. en macOS:
//      sips -s format jpeg -s formatOptions 80 /tmp/capturas/02-lectura-glosa.png --out presentations/capturas/02-lectura-glosa.jpg
// Necesita Google Chrome (o CHROME=/ruta/al/navegador) y `ws` de las dependencias de desarrollo (npm ci --ignore-scripts).
// Las imágenes de terceros (Tlachia, Visual Lexicon) se sustituyen por un recuadro con su crédito: se enlazan, no se copian.
import { createRequire } from 'module';
import { spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';
const require = createRequire(import.meta.url);
const WebSocket = require('ws');

const OUT = process.argv[2];
const BASE = process.argv[3] || 'http://127.0.0.1:8833';
const ONLY = process.argv[4] ? process.argv[4].split(',') : null;
if (!OUT) { console.error('Uso: node presentations/capturas.mjs <carpeta-de-salida> [url] [pasos]'); process.exit(2); }
const W = +(process.env.SHOT_W || 1080), H = 760, DPR = 2;
fs.mkdirSync(OUT, { recursive: true });
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'amoxcalli-capturas-'));
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const chrome = spawn(CHROME, [
  '--headless=new', '--remote-debugging-port=9339', `--user-data-dir=${profile}`, '--no-first-run',
  '--hide-scrollbars', `--window-size=${W},${H}`, '--lang=es-MX', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function target() {
  for (let i = 0; i < 50; i++) {
    try { const r = await fetch('http://127.0.0.1:9339/json'); const l = await r.json(); const p = l.find(t => t.type === 'page'); if (p) return p.webSocketDebuggerUrl; } catch {}
    await sleep(200);
  }
  throw new Error('no chrome');
}
const ws = new WebSocket(await target());
await new Promise(r => ws.on('open', r));
let id = 0; const pending = new Map();
ws.on('message', m => { const d = JSON.parse(m); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } });
const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, d => d.error ? rej(new Error(method + ': ' + d.error.message)) : res(d.result)); ws.send(JSON.stringify({ id: i, method, params })); });
const js = async (expr) => { const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(expr + ' → ' + JSON.stringify(r.exceptionDetails).slice(0, 300)); return r.result.value; };
const waitFor = async (expr, ms = 20000) => { const t = Date.now(); while (Date.now() - t < ms) { if (await js(`!!(${expr})`)) return; await sleep(150); } throw new Error('timeout ' + expr); };

await send('Page.enable'); await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: DPR, mobile: false });
await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'light' }] });

async function go(hash) {
  await send('Page.navigate', { url: BASE + '/' + hash });
  await sleep(600);
  await waitFor(`document.readyState==='complete'`);
  await sleep(800);
}
async function imagesLoaded() { await js(`Promise.all([...document.images].filter(i=>!i.complete).map(i=>new Promise(r=>{i.onload=i.onerror=r;setTimeout(r,8000);})))`); }

// Las imágenes de terceros se ENLAZAN, no se copian (THIRD_PARTY_NOTICES): en la captura se sustituyen por un recuadro con su crédito.
async function maskImages() {
  await js(`(()=>{for(const i of [...document.images]){let h;try{h=new URL(i.src).host}catch{continue}if(!h||h===location.host)continue;
    const r=i.getBoundingClientRect();if(!r.width)continue;const d=document.createElement('div');
    const who=h.includes('tlachia')?'Tlachia (UNAM)':h.includes('wired-humanities')?'Visual Lexicon of Aztec Hieroglyphs':h;
    d.textContent='Imagen enlazada · '+who;d.style.cssText='display:inline-flex;align-items:center;justify-content:center;text-align:center;box-sizing:border-box;width:'+r.width+'px;height:'+Math.max(r.height,40)+'px;border:1.5px dashed #b08a4a;background:#efe6d2;color:#7a5a2a;font:600 '+(r.width<90?9:12)+'px/1.25 system-ui,sans-serif;padding:4px;border-radius:4px';
    i.replaceWith(d);}})()`);
}
// Captura la ventana (opcionalmente desplazada hasta un selector) o el recorte de un elemento.
async function shot(name, { selector, top = 0, pad = 16, full = false, maxH } = {}) {
  await imagesLoaded(); await maskImages(); await sleep(400);
  let clip;
  if (selector) {
    // Varios selectores separados por «|» se unen en un solo recorte.
    const b = await js(`(()=>{const es=${JSON.stringify(selector)}.split('|').map(s=>document.querySelector(s));if(es.some(e=>!e))return null;const rs=es.map(e=>e.getBoundingClientRect());const l=Math.min(...rs.map(r=>r.left)),t=Math.min(...rs.map(r=>r.top)),R=Math.max(...rs.map(r=>r.right)),B=Math.max(...rs.map(r=>r.bottom));return {x:l+scrollX,y:t+scrollY,w:R-l,h:B-t};})()`);
    if (!b) throw new Error('no ' + selector);
    clip = { x: Math.max(0, b.x - pad), y: Math.max(0, b.y - pad), width: b.w + 2 * pad, height: Math.min(b.h + 2 * pad, maxH || 1e9), scale: 1 };
  } else if (full) {
    const h = await js(`document.documentElement.scrollHeight`);
    clip = { x: 0, y: top, width: W, height: Math.min(maxH || h, h - top), scale: 1 };
  } else {
    clip = { x: 0, y: top, width: W, height: maxH || H, scale: 1 };
  }
  const r = await send('Page.captureScreenshot', { format: 'png', clip, captureBeyondViewport: true });
  fs.writeFileSync(path.join(OUT, name + '.png'), Buffer.from(r.data, 'base64'));
  console.log('ok', name, Math.round(clip.width), 'x', Math.round(clip.height));
}
async function typeSearch(text) {
  await js(`(()=>{const i=document.getElementById('search');i.value='';i.focus();})()`);
  await send('Input.insertText', { text });
  await js(`document.getElementById('search').dispatchEvent(new Event('input',{bubbles:true}))`);
  await waitFor(`!document.getElementById('spelling-suggest').hidden && document.querySelector('#spelling-suggest .spelling-option')`);
  await sleep(500);
}
const clickText = (sel, text) => js(`(()=>{const e=[...document.querySelectorAll(${JSON.stringify(sel)})].find(x=>x.textContent.trim().startsWith(${JSON.stringify(text)})||x.getAttribute('aria-label')===${JSON.stringify(text)});if(!e)throw new Error('no '+${JSON.stringify(text)});e.click();})()`);
const scrollTo = (sel, off = 90) => js(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});scrollTo(0,e.getBoundingClientRect().top+scrollY-${off});return scrollY;})()`);


// Marca la sección cuyo encabezado contiene el texto y devuelve su selector.
async function section(text, tag = 'section') {
  const ok = await js(`(()=>{const h=[...document.querySelectorAll('h2,h3')].find(x=>x.textContent.includes(${JSON.stringify(text)}));if(!h)return false;const s=h.closest(${JSON.stringify(tag)})||h.parentElement;s.setAttribute('data-shot',${JSON.stringify(text)});return true;})()`);
  if (!ok) throw new Error('no section ' + text);
  return `[data-shot=${JSON.stringify(text)}]`;
}
const steps = {
  async portada() { await go('#aprender'); await shot('01-portada'); },
  async lectura() {
    await go('#aprender/flor');
    await waitFor(`[...document.querySelectorAll('button')].some(b=>b.getAttribute('aria-label')==='Consultar NIQUITTA')`);
    await clickText('button', 'Consultar NIQUITTA'); await sleep(1500);
    await clickText('button', 'Mostrar glosa interlineal'); await sleep(800);
    const y = await scrollTo('h1', 30);
    await shot('02-lectura-glosa', { top: y, maxH: 1100 });
  },
  async analisis() {
    // Misma página: la hipótesis de análisis automática, con su base.
    const y = await js(`(()=>{const e=[...document.querySelectorAll('*')].find(x=>x.children.length===0&&/ANÁLISIS AUTOMÁTICO · HIPÓTESIS/i.test(x.textContent));return e.getBoundingClientRect().top+scrollY-40;})()`);
    await shot('03-analisis-automatico', { top: y, maxH: 900 });
  },
  async grafias() {
    await go('#grafias');
    await typeSearch('kuali');
    await shot('04-grafias-kuali', { maxH: 640 });
    await shot('04b-kuali-sugerencias', { selector: '#global-search|#spelling-suggest', pad: 14 });
    await go('#grafias/lemma-kwalli');
    await waitFor(`/En cada perfil/.test(document.body.innerText)`);
    await shot('05-grafias-cualli', { top: 150, maxH: 1000 });
    await shot('05b-cualli-perfiles', { selector: await section('En cada perfil'), pad: 20 });
    const y = await js(`(()=>{const e=[...document.querySelectorAll('h2,h3')].find(x=>/Grafías atestiguadas/.test(x.textContent));return e.getBoundingClientRect().top+scrollY-30;})()`);
    await shot('06-grafias-atestiguadas', { top: y, maxH: 900 });
  },
  async dioses() {
    await go('#dioses');
    await typeSearch('Huitzilopoxtli');
    await shot('07-huitzilopoxtli-busqueda', { maxH: 520 });
    await go('#dioses/huitzilopochtli');
    await waitFor(`/Nombres y grafías/.test(document.body.innerText)`);
    await shot('08-huitzilopochtli', { top: 150, maxH: 1050 });
    await shot('08b-huitzilopochtli-grafias', { selector: await section('Nombres y grafías'), pad: 20 });
    await shot('08c-huitzilopochtli-fuentes', { selector: await section('Qué dicen las fuentes'), pad: 20, maxH: 560 });
    await shot('08d-huitzilopochtli-pasajes', { selector: await section('Pasajes del archivo'), pad: 20, maxH: 520 });
    await go('#dioses/veintena-panquetzaliztli');
    await waitFor(`/Dedicada a/.test(document.body.innerText)`);
    await shot('09-panquetzaliztli', { top: 150, maxH: 800 });
    await go('#dioses/calendario');
    await waitFor(`document.querySelector('.gods-signs')`);
    const yt = await scrollTo('#gods-trecena', 30);
    await shot('10-calendario-trecena', { top: yt, maxH: 1000 });
    await go('#dioses/signo-tecpatl');
    await waitFor(`document.querySelector('main img')`);
    await shot('11-signo-tecpatl', { top: 150, maxH: 1000 });
    await shot('11b-tecpatl-glifos', { selector: await section('Glifos en el Telleriano'), pad: 20 });
  },
  async preguntar() {
    await go('#preguntar/' + encodeURIComponent('¿cómo se dice mujer?'));
    await waitFor(`document.querySelector('#ask-results') && /cihuatl/.test(document.getElementById('ask-results').innerText)`, 40000);
    await sleep(1500);
    await shot('12-preguntar-mujer', { top: 150, maxH: 1100 });
    await waitFor(`document.querySelector('.ask-explanation')`);
    await shot('12b-preguntar-explicacion', { selector: '.ask-explanation', pad: 24 });
    await go('#preguntar/' + encodeURIComponent('¿cómo se dice computadora?'));
    await waitFor(`document.querySelector('#ask-results') && document.getElementById('ask-results').innerText.length>40`, 40000);
    await sleep(1200);
    await shot('13-preguntar-abstencion', { top: 150, maxH: 700 });
    await shot('13b-abstencion', { selector: '#ask-results', pad: 20 });
  },
  async proyecto() { await go('#proyecto'); await shot('14-proyecto', { top: 150, maxH: 1000 }); },
};
try {
  for (const [k, f] of Object.entries(steps)) { if (ONLY && !ONLY.includes(k)) continue; await f(); }
} catch (e) { console.error('ERR', e.message); process.exitCode = 1; }
ws.close(); chrome.kill(); fs.rmSync(profile, { recursive: true, force: true });
