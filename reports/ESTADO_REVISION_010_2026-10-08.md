# Diagnóstico conjunto de vigencia de una lectura · ciclo 010

8 de octubre de 2026. Mejora local de solo lectura, implementación serial GPT-6.1 Sol / high, un único escritor. La revisión humana continúa pendiente.

## Problema comprobado

El CLI `lesson_review_packet verify` del ciclo 009 reconstruye la entrega para evitar falsificaciones, pero `checked_hashes` se detiene en la primera fuente cambiada. La inspección de hashes de los históricos mostró una carencia concreta: `aves-009` tenía dos fuentes obsoletas y `aves-009-v2` solo una; ambos comunicaban el mismo primer error de guía y ocultaban la diferencia. Esto dificultaba decidir qué revisar antes de preparar una entrega nueva. No había un comando equivalente que reuniera todas las discrepancias de un paquete explícito.

No se añadió contenido por cuota. Se mantienen los hitos técnicos cubiertos, la entrega autoritativa `aves-009-v1` y las 66 tareas humanas abiertas.

## Fuentes y cambios

Se examinaron el propósito y plan autónomo, el progreso, diagnóstico/cola/estado 009, el informe de revisión 009, el módulo y sus pruebas, y los manifiestos de los tres paquetes existentes. Las referencias públicas del contrato 009 sirven para comprobar hashes; no se copiaron sus filas ni contenidos al nuevo informe.

- Módulo nuevo: `nahuatl_local/lesson_review_status.py`.
- Pruebas nuevas: `tests/test_lesson_review_status.py`.
- Guía nueva: [ESTADO_REVISION_LECTURA.md](../docs/ESTADO_REVISION_LECTURA.md).
- Informes JSON/Markdown nuevos bajo `reports/reading-review-status/`, con sufijo `-010`.

`inspect_package` reúne archivos obligatorios editados/ausentes, miembros extra, manifiesto inválido/no canónico, rutas inseguras y fuentes cambiadas/ausentes con SHA-256 previo y actual. El JSON es determinista; el Markdown usa mensajes en español. Hay tres estados técnicos: `valid`, `stale` e `invalid`. Solo `valid` establece `ready:true`, después de que el **verify original reconstruya y confirme todo**. Las fuentes y archivos vigentes con hashes autodeclarados no bastan: la falsificación semántica con paquete y manifiesto recalculados falla.

Reutiliza `safe_path`, `verify`, `digest` y la codificación determinista. Se comprueban todos los miembros antes de abrir archivos del paquete y todas las rutas de fuente antes de abrir fuentes. Entradas desconocidas/inseguras se rechazan sin publicar su ruta; extras y notas no se leen ni se copian. El preflight acotado también revisa las referencias internas que abriría el legado: `inventory.sources`, evidencias del estado/decisiones y bundles de publicaciones. Una prueba demuestra que inventario o estado falsificados con una referencia pública no registrada no llegan a abrir esa referencia ni a llamar a `verify`.

El registro explícito admite las 61 rutas públicas del contrato 009 y tres referencias de diagnóstico con nombres fijos; ocho rutas de evidencia histórica se reconocen aparte para el preflight. Fuentes/evidencias futuras requieren ampliar el registro y versionar el comando. No hay descubrimiento por carpetas, red ni consulta de URLs. Se conserva el requisito de un único escritor; no se ofrece una instantánea frente a cambios concurrentes.

La salida opcional es un informe nuevo JSON/MD bajo `reports/`, fuera del paquete y de fuentes protegidas. Se reserva también `inventory.json`, `queue.json` y `state.json`. Repetir bytes idénticos devuelve `unchanged`; cambios o notas existentes se conservan y exigen otro nombre. La escritura inicial es exclusiva y no reemplaza archivos existentes. No hay modo de aplicación, importación ni reparación del paquete original.

## Resultados reales

| Paquete | Estado | Causas agregadas | Reconstrucción |
| --- | --- | --- | --- |
| `aves-009` | `stale` | `docs/REVISION_LECTURA.md`, `nahuatl_local/lesson_review_packet.py` cambiados | `not_run` |
| `aves-009-v2` | `stale` | `docs/REVISION_LECTURA.md` cambiada | `not_run` |
| `aves-009-v1` | `valid` | Ninguna discrepancia | `passed` con verify real |

Las seis salidas se repitieron con `unchanged`. [Comprobación de casos reales e idempotencia](status-casos-reales-010.json). Informes legibles: [dos causas del histórico inicial](reading-review-status/aves-009-010.md), [una causa de v2](reading-review-status/aves-009-v2-010.md), [entrega vigente reconstruida](reading-review-status/aves-009-v1-010.md). No se afirma aprobación parcial ni revisión humana para ninguno.

```sh
.venv/bin/python -m nahuatl_local.lesson_review_status --package reports/reading-review/aves-009-v1
.venv/bin/python -m nahuatl_local.lesson_review_status --package reports/reading-review/aves-009 --format md
```

## Pruebas y preservación

[39 pruebas pertinentes](tests-estado-revision-010.txt) pasan en 70,674 s: 15 del primer contrato del nuevo módulo, 12 del paquete 009 y 12 del diagnóstico. Tras el preflight de referencias indirectas y su prueba adicional, las [16 nuevas finales](tests-estado-revision-010-final.txt) pasan en 10,242 s. No se repitió la suite amplia ni se re-midió una batería por este comando.

Las pruebas cubren múltiples causas, contenido distinto con tamaño/mtime iguales, fuentes ausentes, symlinks de miembro/fuente/ancestro, rutas privadas y desconocidas sin lectura ni filtración al informe, esquemas/tipos/campos/hash inválidos, JSON duplicado, manifiesto editado, falsificación semántica con hashes recalculados, referencias internas falsas, no sobrescritura de notas y salidas idempotentes. La comprobación de cierre del fixture coteja los hashes originales protegidos.

El [primer log](tests-estado-revision-010-first.txt) conserva **un fallo entre 15 pruebas** en 10,629 s: cuando una referencia de diagnóstico era un symlink, la validación del grupo descartaba también las otras dos referencias y ocultaba un cambio independiente del estado. Se corrigió separando admisión léxica de los tres roles y preflight individual de sus rutas; el symlink se rechaza y el otro cambio se informa. No se debilitó la reconstrucción ni se modificó el módulo 009.

Se guardaron [baseline 010](iterations/baseline-010.json) y `reports/iterations/state-before-010.json` antes de implementar. El [diagnóstico 010](iterations/iteration-010/inventory.md), su repetición y 009 producen inventario JSON/Markdown y cola byteidénticos. El estado vivo coincide en bytes y semántica con su respaldo; historia, runs, IDs, decisiones, notas y snapshots permanecen intactos. La [comprobación calculada](iteration-repeat-review-status-010-2026-10-08.json) coteja **54 fuentes, 16 archivos protegidos del ciclo 009 y el estado** contra la línea base del coordinador: todos conservan SHA-256. La guía/módulo/tests/informe 009 y los tres paquetes originales no se editaron. Este nuevo módulo/guía no forman parte de las fuentes 009, por lo que `aves-009-v1` conserva vigencia.

Se mantienen 12 lecturas / 48 pasajes, 575 acepciones / 578 formas, 311 apariciones / 9 puentes y 66 tareas humanas abiertas. Batería 123 textual / 51 observaciones de desarrollo más 37 / 15 de reserva, recuperación 119/123, Laboratorio con modelos `not_run` y caché 008 conservan sus bytes y resultados. El diagnóstico vuelve a validar gates existentes; no vuelve a medir rendimiento ni usa la reserva para seleccionar esta mejora.

## Límites y siguiente paso

El informe solo contiene metadata pública, IDs necesarios y hashes; no copia originales, preguntas/claves, filas esperadas/reserva, notas de participantes ni datos privados. La igualdad de hashes permite comprobar bytes; no demuestra revisión humana, fidelidad lingüística, derechos nuevos ni aprendizaje.

La siguiente acción humana sigue siendo revisar los cuatro pasajes de la entrega vigente con una persona competente y evidencia por ID, y acordar después una tarea nueva/rúbrica antes de observar comprensión con principiantes. Si una fuente cambia, conservar paquete/notas y regenerar en una carpeta nueva antes de continuar. Este diagnóstico ayuda a localizar las causas sin resolver esas tareas por software.

No hubo entrenamiento/inferencia, llamadas a modelos, red, lectura de pesos o Voces privado, grandes descargas, pagos, contactos, publicación externa ni commits/push. El servidor habitual no requiere reinicio: el cambio es un CLI local y documentación. El coordinador verificará los tres casos reales y la preservación de forma independiente después de congelar esta entrega.
