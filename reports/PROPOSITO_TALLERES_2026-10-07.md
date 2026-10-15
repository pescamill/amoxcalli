# Propósito, colaboración y talleres

7 de octubre de 2026. Iteración solicitada para revisar utilidad, propósito, colaboración con hablantes y credibilidad institucional.

## Decisiones

El propósito actual es ayudar a comprender fragmentos clásicos con ejemplos documentados. La evaluación debe observar comprensión y consulta de fuentes, no confundir actividad, imágenes o tamaño del catálogo con aprendizaje. Una ruta de variedad actual necesita acuerdos con sus hablantes; el proyecto todavía no ofrece ese curso ni tiene acuerdos comunitarios confirmados.

La colaboración institucional propuesta es revisar cuatro pasajes y probar una lectura acompañada, con responsables, permisos y devolución de resultados. Los criterios y plazos son propuestas del proyecto, no requisitos oficiales. No se envió material ni se obtuvo un aval.

Referencias consultadas: [catálogo INALI](https://www.inali.gob.mx/sitios/clin-inali/) y [diversidad y escritura](https://constitucionenlenguas.inali.gob.mx/lenguas-originarias). Se usaron para fundamentar la separación de variantes, autodenominaciones y participación editorial de hablantes; no se incorporó material lingüístico nuevo de esos sitios.

## Cambios disponibles

- `#proyecto`: propósito, usos según público, inventario dinámico, pendientes y guías descargables.
- `#taller/aves` y las otras lecturas: ficha textual con pasajes originales, preguntas, procedencia, versiones, hashes y notas de derechos. Traducciones y claves son opcionales en impresión. El JSON siempre contiene las claves para revisión y únicamente el contenido público de la lectura.
- Leer enlaza a la ficha; los pasajes enlazan al formulario de cotejo ya existente. No se añade otro sistema de aportaciones ni recogida de notas.
- PROPOSITO, PILOTO_INSTITUCIONAL y CONTRIBUTING ordenan prioridades, participación, acuerdos y revisión. Plantillas de incidencias distinguen contenido y usabilidad.
- README español/inglés, guía web, plan de iteración y dirección histórica reflejan el alcance vigente. Se corrigió la referencia obsoleta al lote batch-009-v11.

## Verificación

- [Python](tests-purpose-2026-10-07.txt): 181 pruebas en 52,929 s, OK con un fallo esperado existente.
- [Interfaz](platform-ui-purpose-2026-10-07.txt): ocho grupos aprobados; se comprueban inventario, claves/traducciones opcionales, procedencia, exportación independiente, conservación del almacenamiento personal y ruta inexistente.
- Las pruebas HTTP comprueban descarga de las tres guías por rutas explícitas y rechazo de rutas arbitrarias; no se expone un directorio de documentación o datos.
- `npm run test:offline`: pasa; no se cachean corpus, perfiles, aportaciones ni solicitudes externas.
- `git diff --check`: sin errores.
- Navegador real: pantalla Proyecto, cifras actuales, acceso a ficha y controles de preparación. El botón de impresión se comprueba en DOM; la calidad del PDF y compatibilidad de impresión deben verificarse en el navegador/dispositivo elegido para un taller.

El corpus, las claves publicadas, el cuaderno personal y los pesos no se modifican. Las pruebas utilizan una base temporal; no se enviaron aportaciones reales. La visibilidad de GitHub tampoco cambia. No hubo entrenamiento ni pruebas con estudiantes en esta iteración.
