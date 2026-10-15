# Una edición de lectura para Scriptorium

7 de octubre de 2026. Actualización de estética y voz escrita a partir de las cinco referencias proporcionadas por el usuario: portadas y páginas de libros de lectura, color e ilustración documental prehispánica.

## Resultado

Cabecera serif, cenefa original, papel cálido y tinta roja. Aprender tiene una portada ocre con el glifo documentado de xochitl y un índice de capítulos; las lecturas conservan márgenes, palabras consultables y notas laterales. Diccionario, cuaderno, archivo, laboratorio, proyecto, talleres y Voces comparten paleta y controles. Se ajustó la voz escrita para invitar a leer y dar acciones concretas. No se añadieron funciones de audio en esta actualización.

La cenefa y el favicon son geometría original. No se copiaron ilustraciones de los libros de referencia ni emblemas institucionales. Las imágenes educativas conservan sus fichas y fuentes; el ornamento no se presenta como un glifo documentado. Las referencias visuales a Teotihuacan no crean afirmaciones de identidad lingüística.

## Preservación

No se modificaron corpus, transcripciones, traducciones, claves, conexiones editoriales ni pesos. El almacenamiento del cuaderno y los permisos no cambian. El estilo se aplica al final de las hojas existentes; conserva la estructura funcional y la impresión textual. Se usan fuentes del sistema y dos SVG originales, sin servicios tipográficos externos. Los iconos raster de instalación y la pantalla de desconexión anterior se conservan.

## Comprobación

- [Interfaz](platform-ui-edition-2026-10-07.txt): ocho grupos aprobados, incluidos lectura, ejercicios, repaso, fuentes, propuestas, laboratorio y fichas de taller.
- [Corpus/HTTP](tests-edition-http-2026-10-07.txt): catorce pruebas pasan.
- `npm run test:offline`: comprobación de privacidad aprobada.
- `git diff --check`: sin errores.
- Navegador real: portada, lectura Flor, ficha del diccionario y Voces. Portada y ficha en ancho 390 px: contenido 375 px, sin desbordamiento horizontal; se restauró el ancho habitual.
- Contrastes calculados sobre papel `#f6f0e2`: texto principal 12,62:1; secundario 5,80:1; rojo 7,82:1; azul 6,59:1. Estos pares no constituyen una auditoría completa de accesibilidad.

Capturas de la comprobación se guardaron en el directorio temporal de trabajo. La [guía de identidad](../docs/IDENTIDAD_EDITORIAL.md) conserva las reglas para continuar esta edición. Los ocho recorridos verifican comportamiento, no certifican las interpretaciones lingüísticas ni el aprendizaje.
