# Validación de la integración

- 13 pruebas de corpus: migraciones, conservación de ediciones locales, permisos, retiro, referencias y rutas HTTP.
- 3 pruebas de archivo: 16,111 pares, filtros, paginación, procedencia, contexto sólo clásico y conservación de variedad al proponer cotejos.
- 13 pruebas de comunidad y 3 de revisión local.
- Flujos DOM/HTTP de investigación y colaboración, incluida subida de WAV y retirada de audio.
- Chromium real: búsqueda, filtros, pantallas de 1360×960 y 390×844 sin desbordamiento horizontal, perfil, respuesta a un texto real y envío de cotejo.
- Dos ejecuciones reales del LLM mediante HTTP, con y sin pasajes en la instrucción. Integración operativa; traducción no fiable. Resultados íntegros conservados, sin sustituirlos por respuestas de reglas.

No se probó un micrófono físico, un despliegue público ni una instalación en Safari/iPhone. Las capturas están en `docs/research-desktop.png`, `docs/research-mobile.png` y `docs/contribute-mobile.png`.
