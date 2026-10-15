# Una lectura lista para entregar a revisión · ciclo 009

8 de octubre de 2026. Preparación local, sin revisión humana realizada. Implementación serial GPT-6.1 Sol / high; un único escritor.

## Problema y carencia comprobada

El propósito prioriza revisar una lectura completa y después observar comprensión con principiantes. Los hitos técnicos están preparados y siguen abiertas 66 tareas humanas. Añadir pasajes por cuota no resuelve ese pendiente.

Se examinaron `lesson_audit`, `editorial_pipeline`, la ficha `#taller/aves` y el protocolo del piloto. La auditoría ya prepara hallazgos y paquetes con original, traducción, anotaciones y ejercicio de reconocimiento. Sin embargo, omite `comprehension`, `context` y `explore_words` que están en la lectura publicada. El JSON de taller sí conserva esos campos, pero no reúne las tareas de la cola vigente, fingerprints de tarea/hallazgo, fichas visuales relacionadas, evidencias de alcance ni una plantilla vacía vinculada a esa cola. El pipeline añade candidatos y decisiones de lote: no sustituye esta entrega de una lectura ya publicada.

Aves es la candidata propuesta en `docs/PILOTO_INSTITUCIONAL.md`; su selección final y el acuerdo de revisión siguen pendientes. Se creó un paquete de revisión complementario, sin otra copia editorial ni cambios al material distribuido.

## Fuentes y cambios

- Módulo nuevo: `nahuatl_local/lesson_review_packet.py`, CLI `prepare` / `verify`.
- Pruebas nuevas: `tests/test_lesson_review_packet.py`.
- Guía nueva: `docs/REVISION_LECTURA.md`.
- Entrega final: [package.md](reading-review/aves-009-v1/package.md), [package.json](reading-review/aves-009-v1/package.json), [plantilla vacía](reading-review/aves-009-v1/human-decisions.blank.json), [manifiesto](reading-review/aves-009-v1/manifest.json).

Reutiliza `Learning.catalog`, la preparación y reconciliación del diagnóstico, los fingerprints existentes y la codificación determinista del pipeline. Trabaja con `CorpusStore` temporal para obtener exclusivamente el catálogo público distribuido. No abre la base privada de Voces. No se modificaron módulos, UI, tests o guías existentes incluidos en los hashes de recuperación/Laboratorio. Ambos README corresponden al coordinador.

La entrega conserva cuatro pasajes: `axolotl-14546`, `axolotl-14253`, `axolotl-08856` y `axolotl-00751`; todos los originales, traducciones, localizadores, URLs, hashes, anotaciones UTF-16, versiones de contenido/práctica, contextos y formas para explorar. Incluye las cuatro preguntas de reconocimiento y cuatro de comprensión ya publicadas, con opciones, claves y explicaciones sin cambios.

Agrupa cinco tareas actuales: `lesson-aves-source-review`, `lesson-aves-exercises`, `lesson-aves-learner-trial`, `word-sense-tototl-glyph-scope` y `batch-visual-policy`. Copia evidencia, aceptación, estado `open`, `finding_fingerprint` y fingerprint de tarea/dependencias; el motivo de inclusión queda explícito. No crea tareas ni cierra ninguna.

Incluye ocho fichas públicas relacionadas: acepción, forma, glifo y cinco fuentes. El glifo `glyph-tototl-mdz46r` mantiene estado `proposed`, verificación `catalog_checked`, contexto de Tototepec / Mendoza f. 46r, créditos y evidencia atribuida. La relación textual `full_word` no se transforma en lectura glífica del pasaje. Las condiciones de cada ficha y los textos se preservan, incluido `training:false`; la exportación no concede permisos nuevos. No se descargan imágenes ni se verifican las URLs remotas.

La plantilla conserva IDs/fingerprints de las cinco tareas, con todos los estados `pending` y campos de responsable, fecha, evidencia, resolución y notas vacíos. La tarea/rúbrica, acuerdos, observaciones y resultados de comprensión también están vacíos. Es un formato de notas, no un archivo de decisiones importable por los flujos existentes. El CLI no tiene acción de aplicación/importación ni marca `reviewed`.

## Vigencia, inmutabilidad y reproducción

El manifiesto reúne 64 entradas públicas de fuente/código/guía/diagnóstico/cola/estado. `prepare` valida hashes y rutas antes de usar las fuentes, reproduce el diagnóstico y la cola, comprueba coherencia con el estado vivo y vuelve a verificar hashes antes de entregar. `verify` comprueba schema y nombres fijos, hashes actuales y reconstrucción semántica; un paquete editado con manifiesto recalculado también falla.

Repetir con entradas idénticas devuelve `unchanged`; un cambio exige directorio nuevo. Se rechazan archivos adicionales, sobrescritura de notas, rutas privadas, salidas fuera de subcarpetas de `reports/`, `..` y enlaces simbólicos en archivos/ancestros. La escritura inicial usa un directorio temporal y traslado del paquete completo. La política de cambios concurrentes sigue requiriendo un único escritor.

```sh
.venv/bin/python -m nahuatl_local.lesson_review_packet prepare --lesson aves --diagnosis reports/iterations/iteration-009 --output reports/reading-review/aves-009-v1
.venv/bin/python -m nahuatl_local.lesson_review_packet verify --output reports/reading-review/aves-009-v1
```

[Log de entrega](package-revision-lectura-009.txt): `prepared`, `unchanged`, `valid`. El primer paquete exploratorio `reports/reading-review/aves-009` se preparó desde 008 antes de congelar código/guía; se conserva como historial de preparación, está obsoleto por sus hashes y no es la entrega vigente. Usar exclusivamente `aves-009-v1` para este ciclo.

## Pruebas y preservación

[37 pruebas pertinentes](tests-revision-lectura-009.txt) pasan en 75,023 s: 12 nuevas y las suites de auditoría, pipeline y diagnóstico. Tras ajustar los rótulos del Markdown al español, las [12 pruebas nuevas finales](tests-revision-lectura-009-final.txt) pasan de nuevo en 21,040 s. Verifican extracción exacta, citas, IDs y offsets, preguntas/claves originales, selección exacta de tareas, alcance/permisos, campos humanos vacíos, vigencia, estado/cola alterados, idempotencia, falsificación con hashes recalculados, no sobrescritura y seguridad de rutas/symlinks.

El [primer log](tests-revision-lectura-009-first.txt) conserva un error entre 12 pruebas: el JSON embebido del Markdown dependía del orden de campos al reconstruir desde JSON. Se corrigió con orden determinista y se repitieron las pruebas. La primera invocación del CLI también falló antes de generar salida por omitir `.md` en `THIRD_PARTY_NOTICES.md`; se corrigió la ruta literal. No se ocultaron fallos ni se atribuyeron a revisión humana.

Se guardó `reports/iterations/state-before-009.json`. [Diagnóstico 009](iterations/iteration-009/inventory.md) y su [repetición](iterations/iteration-009-repeat/inventory.md) son byteidénticos entre sí y con 008. El estado vivo es byteidéntico al respaldo. Se preservan IDs y prefijos de runs, historia, snapshots, notas y decisiones. `editorial/lesson-decisions.json` y las 54 fuentes protegidas por el diagnóstico mantienen sus hashes. La [prueba calculada](iteration-repeat-reading-review-009-2026-10-08.json) registra hashes y comprobaciones. El registro PROGRESO se amplía sin borrar historia.

Se mantienen 12 lecturas / 48 pasajes, 575 acepciones / 578 formas, 311 apariciones / 9 puentes y **66 tareas humanas abiertas**. Batería, reserva, configuración, corpus, recuperación y Laboratorio conservan sus bytes; no se re-midió rendimiento ni se alteraron ranking/resultados. El diagnóstico reproduce validaciones existentes sobre desarrollo como comprobación de vigencia; la reserva no se inspeccionó para elegir esta mejora. El informe de Laboratorio y el estado también coinciden con el baseline independiente del coordinador. Su [verificación independiente](iterations/iteration-009/coordinator-verification.json) registra 19 comprobaciones verdaderas, incluyendo `verify` real, validación completa de Laboratorio sin caché y preservación de los campos originales de anotación junto con sus spans UTF-16 derivados.

## Límites y siguiente paso

No se ha cotejado una edición primaria ni realizado una prueba con personas. Las preguntas existentes de comprensión citan la traducción de origen; copiarlas no demuestra comprensión independiente del náhuatl. No se inventaron rúbricas, claves, revisores, acuerdos ni resultados. Los campos humanos siguen vacíos y la cola permanece abierta.

Antes de la prueba, acordar responsables, permisos, reconocimiento, custodia y retiro conforme al [protocolo existente](../docs/PILOTO_INSTITUCIONAL.md). El siguiente trabajo humano concreto es revisar los cuatro pasajes y sus ayudas/vínculos/derechos con evidencia por ID; después, acordar una tarea nueva y rúbrica con quien facilita, observar dificultades y corregir antes de repetir. Las notas deben guardarse en un archivo nuevo fuera del paquete inmutable y comprobar los fingerprints antes del flujo editorial posterior.

No hubo red, llamadas a modelos, entrenamiento/inferencia, lectura de pesos, grandes descargas, pagos, contactos, publicación externa, commits/push ni modificaciones de `.git`. El servidor habitual no requiere reinicio: este ciclo añade un comando local y documentación, sin cambios en código UI/API cargado.
