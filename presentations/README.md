# Materiales para presentar Amoxcalli

Para buscar especialistas y aliados en México. Todo está escrito a partir de la documentación del repositorio (README, [ROADMAP](../docs/ROADMAP.md), [EVALUACION](../reports/EVALUACION.md), [GRAFIAS](../docs/GRAFIAS.md), [DIOSES_CALENDARIO](../docs/DIOSES_CALENDARIO.md), [PILOTO_INSTITUCIONAL](../docs/PILOTO_INSTITUCIONAL.md), [permisos](../docs/permisos/)) y de la aplicación v0.1.0; las capturas son de la aplicación real. **Nada se ha enviado ni publicado.**

| Entregable | Archivo | Para qué |
|---|---|---|
| 1. Diapositivas (10), español | [diapositivas-es.html](diapositivas-es.html) · [PDF](pdf/diapositivas-es.pdf) | Presentar en una reunión o videollamada |
| 1. Diapositivas (10), inglés | [diapositivas-en.html](diapositivas-en.html) · [PDF](pdf/diapositivas-en.pdf) | Interlocutores que no leen español (la interfaz de la app sigue en español) |
| 2. Guion del video (2:30) | [guion-video.md](guion-video.md) | Grabar el mismo recorrido, toma por toma, con lo que se dice en cada una |
| 3. Mensajes de primer contacto | [mensajes-primer-contacto.md](mensajes-primer-contacto.md) | (a) filología y lingüística, (b) instituciones con fuentes, (c) docentes y comunidades |
| 3. Mensaje institucional, inglés | [mensaje-institucional-en.md](mensaje-institucional-en.md) | (b) para UNAM y para el *Digital Florentine Codex* |
| 4. Hoja de presentación | [hoja-presentacion.html](hoja-presentacion.html) · [PDF](pdf/hoja-presentacion.pdf) | Una página carta: qué es, qué lo distingue, cómo probarlo, qué pedimos |

Recorrido de las diapositivas: el problema → una lectura con análisis y glosa → buscador de grafías (*kuali* → *cualli*) → Huitzilopochtli (grafías, pasajes, veintena; glifos del calendario) → cómo se sostiene cada respuesta → cifras de `reports/EVALUACION.md` → qué falta → qué pedimos → cómo probarlo.

## Uso

- **Presentar:** abrir el HTML en el navegador y avanzar con ← →, espacio o clic. `diapositivas-es.html?todas` muestra todas seguidas. Funciona sin conexión.
- **PDF:** los de `pdf/` se generaron con Chrome (Imprimir → Guardar como PDF; una diapositiva por página de 16:9, la hoja en tamaño carta). Tras editar un HTML, volver a imprimirlo, por ejemplo:
  ```bash
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --no-pdf-header-footer --print-to-pdf="$PWD/presentations/pdf/diapositivas-es.pdf" "$PWD/presentations/diapositivas-es.html"
  ```
- **Antes de enviar o presentar:** completar `[nombre]` y `[correo]` (diapositiva 10, hoja, mensajes) y comprobar las cifras con `make check` si ha pasado tiempo desde el 19 de octubre de 2026.

## Capturas

`capturas/` tiene solo las que usan las diapositivas y la hoja, tomadas el 19 de octubre de 2026 con la aplicación local (`bash scripts/amoxcalli.sh serve`). Para regenerarlas: [capturas.mjs](capturas.mjs) (instrucciones al inicio del archivo).

**Las imágenes de terceros no se copian.** Los glifos de Tlachia (UNAM) y del Visual Lexicon of Aztec Hieroglyphs se cargan desde sus sitios en la aplicación; en las capturas aparecen como un recuadro con su crédito, igual que el proyecto los enlaza sin redistribuirlos ([THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md)). En una presentación en vivo o en el video se ven como las ve cualquier persona usuaria.

## Cuidado con lo que se afirma

- No mencionar aval, convenio ni colaboración con UNAM, INALI, IDIEZ, Getty ni ninguna institución, ni usar sus logotipos: no los hay.
- Las cifras son técnicas, sobre conjuntos pequeños escritos por el equipo; decirlo siempre que se cite una.
- Lo automático está pendiente de revisión lingüística; ninguna persona especialista ha firmado una revisión.
- La carta a la UNAM ([unam-gdn-tlachia.md](../docs/permisos/unam-gdn-tlachia.md)) habla de 13 láminas de Tlachia; hoy son 21 (480 apariciones). Actualizarla antes de enviarla.
- Las fichas de dioses ocultan los pasajes de obras que esperan permiso (18 en Huitzilopochtli), pero Preguntar y el análisis de palabras sí muestran pasajes de *Vida económica de Tenochtitlan*. Por eso los materiales limitan esa afirmación a las fichas de dioses; no generalizarla.
