"use strict";
// El Python de Amoxcalli dentro del navegador: el mismo código del servidor (nahuatl_local/movil.py), sin red.
importScripts('pyodide/pyodide.js');

const estado = (texto, listo = false) => postMessage({ estado: texto, listo });
const sync = (py, populate) => new Promise((resolve, reject) => py.FS.syncfs(populate, e => (e ? reject(e) : resolve())));

let python = null;
const ready = (async () => {
 estado('Preparando Python…');
 const py = await loadPyodide({ indexURL: new URL('pyodide/', location.href).href });
 await py.loadPackage('sqlite3');
 estado('Cargando lecturas y diccionario…');
 const zip = await (await fetch('amoxcalli.zip')).arrayBuffer();
 py.unpackArchive(zip, 'zip', { extractDir: '/amoxcalli' });
 // Lo tuyo (aclaraciones, perfil) vive en IndexedDB de este navegador; lo demás viene del paquete.
 const datos = '/amoxcalli/data/community';
 py.FS.mkdirTree(datos);
 py.FS.mount(py.FS.filesystems.IDBFS, {}, datos);
 await sync(py, true);
 py.runPython("import sys\nsys.path.insert(0, '/amoxcalli')\nfrom nahuatl_local.movil import App\napp = App()");
 await sync(py, false);
 python = py;
 return py;
})();

function atender({ id, method, path, body, type }) {
 const app = python.globals.get('app');
 const result = app.request(method, path, body ? new Uint8Array(body) : '', type);
 const [status, headers, payload] = result.toJs();
 result.destroy();
 app.destroy();
 postMessage({ id, status, headers, body: payload.buffer }, [payload.buffer]);
 if (method !== 'GET') sync(python, false).catch(() => {});
}

onmessage = async ({ data }) => {
 try {
  if (!python) await ready;
  atender(data);
 } catch (error) {
  postMessage({ id: data.id, error: 'Amoxcalli no pudo responder: ' + String(error.message || error).split('\n').slice(-2).join(' ') });
 }
};

// Preparación del análisis, etapa por etapa: entre una y otra se atienden las consultas que lleguen.
ready.then(async py => {
 estado('', true);
 const etapas = py.globals.get('app').warm_stages();
 for (const etapa of etapas) {
  await new Promise(resolve => setTimeout(resolve, 0));
  try { etapa(); } catch { break; }
 }
}).catch(error => estado('No se pudo abrir Amoxcalli en este navegador: ' + String(error.message || error).split('\n').slice(-2).join(' ')));
