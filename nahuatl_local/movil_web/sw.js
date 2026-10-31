"use strict";
// Amoxcalli sin internet: la primera visita guarda la app completa (Python, lecturas y diccionario) en el
// dispositivo; después todo se abre desde ahí. Cada versión publicada trae su propia lista de archivos.
const CACHE = 'amoxcalli-movil-__VERSION__';
const FILES = __FILES__;

self.addEventListener('install', event => event.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())));
self.addEventListener('activate', event => event.waitUntil(caches.keys()
 .then(keys => Promise.all(keys.filter(k => k.startsWith('amoxcalli-movil-') && k !== CACHE).map(k => caches.delete(k))))
 .then(() => self.clients.claim())));
self.addEventListener('fetch', event => {
 const url = new URL(event.request.url);
 if (event.request.method !== 'GET' || url.origin !== self.location.origin || !url.pathname.startsWith(new URL('./', self.location).pathname)) return;
 event.respondWith(caches.open(CACHE)
  .then(c => c.match(event.request, { ignoreSearch: true }))
  .then(hit => hit || fetch(event.request)));
});
