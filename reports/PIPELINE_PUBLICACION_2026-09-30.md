# Pipeline editorial operativo · 30 de septiembre de 2026

Se completó el flujo por lotes: extracción determinista, prioridad por grafía escrita, cotejo de fuentes, excepciones, ensamblado y publicación aditiva. El script no usa LLM. El objetivo es ampliar el material disponible para aprender mediante ejemplos y reservar el trabajo editorial para las interpretaciones que necesitan criterio lingüístico.

## Publicado en la app

El lote `batch-007-v9` añade **50 acepciones, 50 formas y 39 referencias contextuales**. Las 50 transcripciones coinciden con las filas cacheadas de Molina 2/GDN; cada apoyo visual conserva imagen, crédito y lectura de su referencia y evidencia de definición o coocurrencia en un par clásico. Las 89 comprobaciones aceptadas declaran su alcance automático. No se afirma cotejo primario ni equivalencia glífica de toda la palabra.

| Estado | Antes | Después |
|---|---:|---:|
| Entidades | 1.178 | 1.317 |
| Acepciones | 525 | 575 |
| Formas | 528 | 578 |
| Referencias glíficas | 101 | 140 |
| Acepciones con imagen | 100 | 139 |
| Imágenes documentales distintas | 24 | 24 |

Se preservaron las 1.178 filas previas con versiones/fechas, relaciones, historial, perfiles, aportaciones, audio, revisiones y propuestas de entrenamiento. [Comprobación](publication-batch-007-v9.json). Respaldo privado 0600: `data/backups/voces-before-batch-007-v9.sqlite3`. El [registro de publicaciones](../corpus/editorial-releases.json) distribuye el lote con SHA256; no reemplaza ediciones locales y una segunda ejecución no duplica registros.

Los textos originales, ejercicios, progreso de aprendizaje y modelos permanecen intactos. Las 24 palabras representativas siguen en la primera página; las otras 551 acepciones aparecen por orden alfabético náhuatl. El navegador real confirmó 575 entradas y 139 con imagen después de reiniciar y actualizar la app.

## Continuación preparada

[Lote batch-008-v10](editorial-pipeline/batch-008-v10/README.md): 50 entradas, 4 apoyos contextuales, 100 concordancias y paquetes de las 3 lecciones / 26 tareas (1 resuelta, 4 bloqueadas, 21 abiertas). Las mismas páginas cacheadas ofrecen 322 entradas elegibles y el lote selecciona 50; las otras 272 quedan para siguientes pasadas. Preparación, cotejo y ensamblado usaron cero red y cero LLM. **Este segundo lote todavía no se publicó.**

```bash
.venv/bin/python -m nahuatl_local.editorial_pipeline run --release-id batch-008-v10
# Para incorporar el lote, con el servidor temporalmente detenido:
.venv/bin/python -m nahuatl_local.editorial_pipeline run --release-id batch-008-v10 --apply
```

Usar otro ID para otro lote. El comando procesa conjuntamente las fuentes y los paquetes; no requiere repetir una investigación por palabra. [Guía](../docs/EDITORIAL_PIPELINE.md).

## Qué queda para la revisión editorial

436 de las 575 acepciones todavía no tienen imagen documentada en el inventario disponible. Las nuevas conexiones son apoyos contextuales y mantienen revisión lingüística/primaria pendiente. Las 10 acepciones objetivo de las lecciones actuales tienen imagen; 0/10 declaran cotejo primario. NIQUITTA, xochitli y tlacuilolcalli siguen sin fichas exactas en sus acepciones anotadas.

Las concordancias y propuestas de anotación no asignan una acepción automáticamente ni publican nuevas lecciones. Los paquetes agrupan pasajes originales, faltantes y decisiones para completar ese trabajo. Los ensayos con principiantes siguen preparados, sin participantes registrados. Ninguna ficha nueva concede entrenamiento ni altera reservas de validación/prueba.

## Validación

[175 pruebas Python](tests-pipeline-release-full-2026-09-30.txt): OK, con una falla esperada preexistente. Incluyen siete pruebas nuevas de cotejo y publicación y ocho de preparación/ensamblado. Verifican caché alterada, dependencias cambiadas, conservación de fichas y datos privados, instalación nueva, hashes, repetición del comando y recuperación tras una interrupción del registro. [Interfaz DOM/HTTP](platform-ui-pipeline-release-2026-09-30.txt) y comprobación del diccionario en el navegador real.
