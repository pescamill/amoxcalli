# De la lectura a la consulta y al repaso

Entrega local del 7 de octubre de 2026, basada en el [recorrido por la interfaz](RECORRIDO_USUARIO_2026-10-07.md).

## Cambios

- El diccionario prioriza coincidencias exactas. Si una palabra no tiene entrada, ofrece buscar sus testimonios en el archivo. La primera página representativa mantiene su selección.
- Cada lectura permite copiar una palabra y consultar el archivo o el diccionario. Aves ofrece atajos tomados literalmente de los cuatro pasajes, sin inventar glosas.
- Al guardar una palabra desde una lectura, Mis palabras conserva su pasaje de origen y permite volver a leerlo. Una palabra ya guardada puede recibir contexto sin perder su calendario de repaso. El navegador almacena el ID del registro; las citas se resuelven contra las lecturas actuales.
- Aves añade cuatro preguntas de comprensión con respuestas citadas de las traducciones originales. El reconocimiento anterior se conserva y la comprensión se registra por separado. La respuesta incorrecta invita a revisar el fragmento.
- Voces mantiene la navegación Aprender y pide elegir experiencia, sin seleccionar de entrada fluidez desde la infancia.

## Publicación y preservación

Se aplicó la [receta](../configs/reading-context-2026-10-07.json) mediante `lesson_builder`, con [propuesta verificable](../editorial/reading-context-2026-10-07.json) y [respaldo](learning-before-reading-context-2026-10-07/learning-v1.json). Permanecen seis lecturas y 24 ejemplos; los pasajes, sus hashes y los ejercicios originales se conservan. Aves cambia a versión de contenido 2 y mantiene versión de práctica 1.

El lote preparado batch-009-v11 corresponde al hash anterior de lecturas. Para continuar la ampliación léxica hay que preparar un lote nuevo y revisar sus resultados antes de publicar. Las preguntas nuevas están sujetas a revisión lingüística, como el resto del piloto. Esta entrega no entrena ni modifica el LLM.

## Comprobación

- [Suite Python](tests-reading-context-2026-10-07.txt): 181 pruebas, OK; un fallo esperado de una regla ortográfica deshabilitada.
- [Interfaz](platform-ui-reading-context-2026-10-07.txt): siete grupos de recorridos pasan, incluidos búsquedas, comprensión, migración del cuaderno y contexto del repaso. Las aportaciones se prueban en una base temporal.
- `npm run test:offline`: pasa la comprobación de privacidad de la caché.
- `git diff --check`: sin errores.
- Navegador real: reconocimiento previo conservado, vínculo de `tototl` guardada al primer pasaje, cita visible en Mis palabras, regreso a la lectura y consulta de palabras no anotadas. No se enviaron aportaciones.

Para repetir la prueba de interfaz: `npm ci --ignore-scripts` y `npm run test:ui`. Node se usa para estas comprobaciones; la aplicación conserva su arranque con Python.
