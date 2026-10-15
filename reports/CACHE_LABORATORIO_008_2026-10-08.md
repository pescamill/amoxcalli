# Caché validada del Laboratorio · ciclo 008

8 de octubre de 2026. Mejora acotada de latencia local; los resultados documentales y los pendientes humanos se conservan.

## Problema comprobado y cambio

Cada resumen o descarga pública del Laboratorio volvía a reproducir las 123 consultas del informe de recuperación y crear una base pública temporal. El coordinador midió tres descargas del mismo informe en el servidor habitual: 2,1491575 s, 2,1583464 s y 2,0465080 s; media 2,118004 s y payload idéntico. [Medición previa](documentary-laboratory-experiments/iteration-008/http-baseline.json).

`nahuatl_local/documentary_laboratory.py` conserva ahora en memoria únicamente la proyección pública validada, con un máximo de cuatro raíces y expulsión LRU. La primera carga sigue validando y reproduciendo recuperación. El bloqueo compartido impide reproducciones simultáneas duplicadas y las respuestas llevan copias profundas, de modo que una persona llamadora no puede modificar lo retenido.

Cada acceso vuelve a comprobar rutas públicas, enlaces simbólicos y SHA-256 de los archivos dependientes, incluido el informe completo, la evidencia DOM y las fuentes de reconstrucción de la batería. No se confía en tamaño, mtime o una caducidad. La batería también depende de `corpus/learning-v1.json`, que no figura en el manifiesto del ranker; se añadió explícitamente a la firma de caché a través de los inputs fijos del evaluador. Cambios, ausencias o rutas inseguras invalidan la reutilización antes de responder; un cambio durante la validación se rechaza mediante hashes anteriores/posteriores.

Solo se retiene un resumen con presentación vigente. Si falta evidencia DOM, el comportamiento anterior sigue mostrando los resultados documentales válidos con `ready:false`, sin reutilizar una presentación previa. Un identificador de descarga desconocido se rechaza antes de leer o reproducir. El validador completo, CLI y gate de iteración permanecen sin caché.

No se guardan respuestas esperadas, claves de reserva, bases, perfiles privados ni estado de modelos. La caché no altera almacenamiento HTTP persistente, service worker, contenido, ranking, UI ni costes históricos.

## Medición reproducible

El [script local](documentary-laboratory-experiments/iteration-008/measure-latency.py), ejecutado desde la raíz con `.venv/bin/python`, mide con `time.perf_counter` y cuenta llamadas al validador de recuperación. [Artefacto final](documentary-laboratory-experiments/iteration-008/in-process-latency.json): primera carga 2,1190366 s; cinco resúmenes posteriores 9,25–9,51 ms; seis descargas 9,48–9,79 ms. Hubo **una reproducción en doce operaciones**, con payloads idénticos para cada operación repetida.

El coordinador refrescó el servidor habitual con el mismo comando y configuración y midió el mismo endpoint de comparación: primera descarga 2,023461 s; cinco posteriores 9,426, 9,285, 9,659, 9,169 y 9,161 ms, media **9,33997 ms**. Todos los payloads de esa corrida son idénticos. Runs, batería, derechos, revisión humana, comparación, alcance y limitación coinciden exactamente con el snapshot 007; cambian los hashes de código/presentación. [Verificación HTTP independiente](documentary-laboratory-experiments/iteration-008/http-after.json).

Son muestras pequeñas locales: tres descargas previas y cinco posteriores en HTTP, más la medición en proceso. Incluyen efectos de filesystem caliente y no garantizan tiempos de otro equipo. Miden latencia de informes, sin evaluar calidad lingüística, comprensión, modelos ni coste monetario. Los tiempos/costes observados de recuperación permanecen intactos.

## Pruebas y correcciones

- **50 pruebas dirigidas, OK**, incluidas nueve de caché: una reproducción para resúmenes/descargas múltiples, copia defensiva, CLI caliente independiente, contenido modificado con igual tamaño/mtime, alteración del informe, dependencia de lectura, evidencia DOM cambiada/ausente, archivos ausentes, enlaces simbólicos, ruta privada rechazada antes de abrir, aislamiento de raíces, límite de tamaño, cuatro primeras solicitudes concurrentes y descarga inválida temprana. [Log final](tests-laboratory-final-directed-008.txt).
- **11 grupos DOM/HTTP, OK** con evidencia final persistida después de pasar toda la suite. [Log final](platform-ui-laboratory-final-008-localhost.txt). [Privacidad offline, OK](offline-laboratory-008.txt): sin corpus, perfiles, envíos ni peticiones externas en caché persistente.
- [CLI completo final](documentary-laboratory-validation-final-008.txt), vigente y sin caché. Diagnóstico y repetición reproducen los tres gates válidos.

Se conserva el [primer log dirigido fallido](tests-laboratory-directed-008.txt): las copias temporales omitían la dependencia de lecturas y siete pruebas rechazaron correctamente esos inputs incompletos. La corrección amplió tanto el fixture como la firma efectiva de caché, sin debilitar el validador. El error HTTP restante y el [primer DOM bloqueado](platform-ui-laboratory-008.txt) fueron binds localhost rechazados por sandbox; la repetición con aprobación automática sobre base y servidor sintéticos pasó. La interrupción por límite de uso retrasó este mismo ciclo; las activaciones pendientes no se cuentan como entregas.

## Preservación y estado final

Antes de cambiar código se congelaron informe, evidencia de pantalla y recuperación de 007 en [snapshots](documentary-laboratory-experiments/iteration-008/snapshot-hashes.json), además del [estado previo](iterations/state-before-008-2026-10-08.json). El informe actual de recuperación conserva SHA-256 `94ef70f05f356aa9811000ed1298a8eca22d0eaa82295756152ea336864c3e9b`: no hubo nueva medición ni ajuste de ranking/batería/reserva.

Se actualizaron solamente informe Lab y evidencia DOM para los nuevos hashes. Informe Lab final: `cfe7a02b879de24e0142d62506ccc43bf7a587dc95953f38abf9988f1d47dd3d`; evidencia DOM: `03a094985925759783be45a310a72184b57b2b2b151e7240d928555ab4203dc1`.

[iteration-008](iterations/iteration-008/inventory.md) y su repetición tienen inventario JSON/Markdown, cola y estado **idénticos en bytes**. Se conservan todos los IDs, estados y decisiones, los prefijos de historia, runs, notas y snapshots; coinciden el manifiesto vigente y los hashes de corpus, batería y derechos. [Comprobación calculada](iteration-repeat-cache-laboratory-008-2026-10-08.json).

Permanecen 12 lecturas/48 pasajes, 575 acepciones/578 formas, 311 apariciones y 9 puentes léxicos. Recuperación mantiene 119/123 completas, 121 con resultados y citas válidas, 840/860 campos exactos, dos parciales y dos abstenciones. Hay **66 tareas humanas abiertas**. La ruta textual/multimodal sigue `not_run`; ningún hito humano se marca resuelto.

No se entrenó, consultó ni descargó un modelo; no se abrieron pesos ni Voces privado, evaluó la reserva, descargó imágenes, pagó, contactó a personas, publicó fuera del equipo, hizo commit o push. La siguiente acción sigue siendo revisar una lectura con una persona competente y probar comprensión con principiantes, con responsable y evidencia. Los derechos y el presupuesto deben acordarse antes de una corrida de modelo.
