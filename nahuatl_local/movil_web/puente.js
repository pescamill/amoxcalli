"use strict";
// Amoxcalli sin servidor: lo que la página pide a api/ lo atiende Python (Pyodide) en un worker de este navegador.
// La interfaz es la misma de la versión de computadora; solo cambia quién responde.
(() => {
 const base = new URL('./', location.href);
 const api = new URL('api/', base).pathname;
 const worker = new Worker(new URL('worker.js', base));
 const pending = new Map();
 let next = 0;

 // Arranque: la primera vez descarga Python y las lecturas (~20 MB); después abre desde el dispositivo.
 const style = document.createElement('style');
 style.textContent = '.movil-arranque{position:fixed;inset:0;z-index:99;display:grid;place-content:center;gap:6px;text-align:center;padding:24px;background:#f6f0e2;color:#2b211c;font:16px/1.4 system-ui,sans-serif}.movil-arranque>*{max-width:34em;overflow-wrap:anywhere}.movil-arranque b{font:600 32px/1.1 Georgia,serif;color:#812d37}.movil-arranque small{color:#6b5d52}';
 document.head.append(style);
 const veil = document.createElement('div');
 veil.className = 'movil-arranque';
 veil.setAttribute('role', 'status');
 veil.innerHTML = '<b>Amoxcalli</b><span data-estado>Abriendo…</span><small>La primera vez descarga unos 20 MB; después funciona sin internet.</small>';
 const show = () => document.body.append(veil);
 document.body ? show() : document.addEventListener('DOMContentLoaded', show);

 worker.onmessage = ({ data }) => {
  if ('estado' in data) {
   veil.querySelector('[data-estado]').textContent = data.estado;
   if (data.listo) veil.remove();
   return;
  }
  const p = pending.get(data.id);
  if (!p) return;
  pending.delete(data.id);
  if (data.error) p.reject(new TypeError(data.error));
  else p.resolve(new Response(data.status === 204 ? null : data.body, { status: data.status, headers: data.headers }));
 };

 const original = window.fetch.bind(window);
 window.fetch = async (input, init = {}) => {
  const request = input instanceof Request ? input : null;
  const url = new URL(request ? request.url : input, location.href);
  if (url.origin !== location.origin || !url.pathname.startsWith(api)) return original(input, init);
  const method = (init.method || request?.method || 'GET').toUpperCase();
  let body = init.body ?? (request && method !== 'GET' ? await request.arrayBuffer() : null);
  if (body instanceof Blob) body = await body.arrayBuffer();
  else if (typeof body === 'string') body = new TextEncoder().encode(body).buffer;
  const type = new Headers(init.headers || request?.headers).get('content-type') || 'application/json';
  const id = next++;
  return new Promise((resolve, reject) => {
   pending.set(id, { resolve, reject });
   worker.postMessage({ id, method, path: '/api/' + url.pathname.slice(api.length) + url.search, body, type }, body ? [body] : []);
  });
 };

 if ('serviceWorker' in navigator) navigator.serviceWorker.register(new URL('sw.js', base)).catch(() => {});
})();
