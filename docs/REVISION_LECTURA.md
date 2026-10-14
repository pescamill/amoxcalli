# Preparar una lectura para revisión humana

Este comando local reúne una sola lectura publicada, sus pasajes originales, ejercicios de reconocimiento y comprensión con las claves y explicaciones existentes, anotaciones, contexto y formas para explorar. Añade las tareas pertinentes de la cola vigente, sus IDs y fingerprints, las fichas visuales y sus fuentes/permisos. No hace una traducción nueva, no prueba comprensión con personas ni registra revisión especializada.

La ficha de `#taller/aves` ya ofrece impresión y JSON con claves. Los paquetes de `lesson_audit` y `editorial_pipeline` ya ofrecen hallazgos y evidencia. Esta entrega los complementa: la auditoría omite `comprehension`, `context` y `explore_words`, y la ficha del taller no agrupa cola, alcance visual y decisiones pendientes. El comando reutiliza `Learning.catalog`, `iteration.diagnose`, reconciliación y codificación del pipeline; conserva ambos fingerprints (hallazgo editorial y tarea con dependencias). No cambia esos módulos ni la interfaz.

Desde la raíz del proyecto:

```sh
.venv/bin/python -m nahuatl_local.iteration --output reports/iterations/iteration-009
.venv/bin/python -m nahuatl_local.lesson_review_packet prepare --lesson aves --diagnosis reports/iterations/iteration-009 --output reports/reading-review/aves-009-v1
.venv/bin/python -m nahuatl_local.lesson_review_packet verify --output reports/reading-review/aves-009-v1
```

`prepare` requiere diagnóstico, cola y estado actuales coherentes entre sí. Reproduce el diagnóstico y la cola sin escribirlos, comprueba SHA-256 de las fuentes antes y después y trabaja únicamente con el catálogo público en una base temporal. Repetir con entradas idénticas devuelve `unchanged`. El comando no recibe catálogos privados, no usa red, pesos ni modelos y no selecciona mejoras con claves de reserva.

El directorio contiene:

- `package.json`: lectura completa, tareas actuales con evidencia y motivos de selección, fichas de catálogo relacionadas y condiciones de uso. Las relaciones textuales (`full_word`, etc.) siguen separadas del estado y contexto de la ficha visual.
- `package.md`: documento legible con los cuatro pasajes de Aves, localizadores, preguntas/claves/explicaciones y evidencia visual. Las URLs se conservan como referencias; no se descargan imágenes.
- `human-decisions.blank.json`: campos humanos vacíos, estado `pending`, IDs/fingerprints copiados y espacios vacíos para acuerdos, tarea/rúbrica y resultados de una futura prueba. Es una plantilla de notas, no el formato de importación de `iteration` o `lesson_audit`.
- `manifest.json`: hashes de archivos del paquete y de entradas públicas, código y guías. Verificar reconstruye el contenido además de comprobar hashes.

Antes de usarlo, ejecutar `verify`. Si cambiaron fuentes, cola, estado, código, guía o archivos del paquete, falla y exige un directorio nuevo; no sobrescribe decisiones ni borradores. Rechaza rutas privadas, rutas fuera del proyecto, `..`, enlaces simbólicos en archivo/ancestros y archivos adicionales. Las salidas se permiten solo en subcarpetas de `reports/`. La comprobación es local y no acredita vigencia remota ni nuevos derechos. Como el estado vivo se incluye en el manifiesto, un diagnóstico posterior que cambie ese archivo exige una preparación nueva aunque Aves no haya cambiado.

Para una revisión real, copiar la plantilla a un archivo nuevo fuera del directorio inmutable y registrar únicamente decisiones efectivas con responsable autorizado, fecha y evidencia/localizador. Dejar las dudas pendientes. Ningún comando de esta guía importa o aplica esas notas, cambia `editorial/lesson-decisions.json`, marca `reviewed` ni cierra tareas humanas. La incorporación editorial posterior requiere el flujo correspondiente y cotejo del fingerprint.

El [piloto institucional](PILOTO_INSTITUCIONAL.md) conserva el protocolo propuesto: acordar responsables, permisos, reconocimiento, custodia y retiro antes de una actividad con personas; revisar cuatro pasajes y derechos; elegir una tarea nueva y rúbrica con el docente; observar dificultades y corregir antes de repetir. No hay participantes, revisores, acuerdos ni prueba realizados por esta preparación. Las preguntas actuales se apoyan en la traducción de origen y no sustituyen esa tarea nueva.
