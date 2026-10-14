# Pipeline editorial por lotes

Implementado el 30 de septiembre de 2026. Sustituye la investigación manual repetida por un procesamiento conjunto de lecciones, catálogo y fuentes. El LLM no participa. La revisión conserva su alcance: una transcripción de diccionario o una comparación visual no certifican todas las interpretaciones lingüísticas de un pasaje.

## Continuar con un comando

Desde la raíz del proyecto:

```bash
.venv/bin/python -m nahuatl_local.editorial_pipeline run --release-id batch-010-v12
```

Este lote ya está preparado y cotejado. El comando vuelve a comprobar la evidencia y el catálogo, sin duplicar ni publicar registros. Para incorporarlo, detener temporalmente el servidor y ejecutar:

```bash
.venv/bin/python -m nahuatl_local.editorial_pipeline run --release-id batch-010-v12 --apply
```

Después, reiniciar la plataforma. `--apply` añade el lote a la base local y a la distribución, con un respaldo 0600 y un informe de preservación. No requiere investigación manual por palabra. Si el lote ya está publicado, devuelve `already_published`; las instalaciones nuevas lo cargan sin reemplazar ediciones locales.

Para otro lote, usar un ID nuevo, por ejemplo `batch-010-v12`. `run` reúne **preparar → cotejar → ensamblar → publicar si se indicó `--apply`**. Por defecto reutiliza la caché; `--fetch` descarga solo páginas ausentes. Las salidas quedan en `reports/editorial-pipeline/ID/` y `editorial/ID-{source-check,accepted}.json`. Un lote ya preparado es inmutable; nuevos datos requieren otro ID.

El cotejo automatizado comprueba transcripciones literales y apoyos contextuales explícitos. **No acredita análisis lingüístico, lectura completa del glifo ni cotejo primario.** Las fichas mantienen estos estados pendientes. Las conexiones forma→acepción dentro de un pasaje y las nuevas lecciones permanecen en los paquetes editoriales para revisión.

## Un comando para preparar el lote

Desde la raíz del proyecto:

```bash
.venv/bin/python -m nahuatl_local.editorial_pipeline prepare \
  --output reports/editorial-pipeline/mi-lote-001
```

El comando usa el catálogo distribuido, las lecciones actuales y la caché de GDN. Para obtener páginas faltantes de las fuentes registradas, añadir `--fetch`. No repite descargas ya almacenadas. La [configuración](../configs/editorial-pipeline.json) limita cada lote a 50 entradas léxicas y 100 concordancias; agrupa búsquedas por prefijo, hasta ocho en el plan generado. Los prefijos organizan consultas del catálogo; no se interpretan como raíces.

Para incluir cambios ya aceptados en tu catálogo local, exporta una instantánea pública y pásala al pipeline:

```bash
.venv/bin/python -m nahuatl_local.platform export --purpose research \
  --output editorial/catalog-public-pipeline-001.json
.venv/bin/python -m nahuatl_local.editorial_pipeline prepare \
  --catalog editorial/catalog-public-pipeline-001.json \
  --output reports/editorial-pipeline/mi-lote-002
```

`prepare` trabaja con una base temporal y no abre la base privada. Un archivo `--catalog` debe ser público, válido y sin fichas retiradas. El exportador conserva sus comprobaciones habituales de permisos. Los nombres de salida deben ser nuevos: repetir exactamente los mismos datos devuelve `unchanged`; un cambio requiere otra carpeta. No se sobrescriben borradores ni decisiones.

## Qué automatiza

| Etapa | Resultado | Trabajo humano restante |
|---|---|---|
| Auditar todas las lecciones | Vacíos, claves, hashes, dependencias y un paquete bilingüe por lección | Cotejo primario y explicaciones lingüísticas |
| Leer fuentes en bloque | Páginas GDN cacheadas, hashes y filas originales | Revisar fuente/alcance una vez por grupo |
| Preparar entradas | Paleografía, grafía normalizada y glosa histórica separadas; duplicados excluidos | Resolver formas con prefijos, remisiones y otros casos que el parser excluye |
| Priorizar | Primero grafías escritas completas presentes en lecciones, después frecuencia de esa forma en el corpus | Decidir utilidad pedagógica y polisemia |
| Preparar conexiones visuales | Referencias documentales/contextuales declaradas, con dependencias válidas | Revisar lectura, componente y contexto; no inferirlos por compartir letras |
| Proponer apoyos de lectura | Formas no anotadas con coincidencias exactas o ambiguas del catálogo | Elegir la acepción adecuada en el pasaje; las propuestas no se aplican automáticamente |
| Obtener concordancias | Hasta 100 formas recurrentes con ejemplos y reservas de evaluación conservadas | Definir lema/acepción; los tokens no se convierten en lemas automáticamente |
| Revisar por grupos | Una decisión compartida y excepciones individuales | Registrar responsable, fecha, evidencia y alcance |
| Cotejar | Texto literal GDN y evidencia contextual comparados con caché/archivo; excepciones diferidas | Resolver casos que no pasan el cotejo y validar interpretaciones lingüísticas |
| Ensamblar | JSON validado que solo añade IDs nuevos | Revisar el alcance y las excepciones |
| Publicar | Respaldo, preservación y migración distribuida aditiva | Revisar y probar una lección antes de declararla completa |

Las páginas que alcanzan el límite de resultados y las ausentes se identifican. Un prefijo con cero resultados no prueba que la palabra no exista en otras fuentes. Una página inesperada detiene el lote; no se interpreta como búsqueda vacía. El pipeline no inventa traducciones, imágenes, segmentaciones o pruebas con personas.

## Archivos para revisar

Abrir `README.md` en la carpeta generada. Los archivos principales son:

- `dictionary-candidates.json` y `lexical-priorities.json`: hasta 50 entradas y su prioridad, preservando la escritura original.
- `visual-candidates.json` y `visual-inventory.json`: apoyos propuestos y faltantes; cobertura de candidatos separada de publicación/revisión.
- `review-groups.json`: grupos de transcripciones y referencias visuales. Cada grupo incluye fingerprints de sus elementos.
- `review-items.json`: evidencia de cada candidato y fingerprint; sirve para registrar excepciones al grupo.
- `concordances.json`: 100 candidatos de lectura con grafías observadas y fuentes; no asigna una definición automática.
- `annotation-candidates.json`: posibles palabras para destacar en las lecciones actuales, sin modificar los originales.
- `lesson-queue.json`, `lesson-inventory.md` y los `*-packet.json`: revisión de las lecciones con las decisiones existentes.
- `sources.json`: hashes, resultados, páginas ausentes/truncadas y motivos de exclusión.
- `next-source-config.json`: configuración para el siguiente lote. Si aún hay entradas elegibles pendientes por el límite del lote, reutiliza las mismas fuentes cacheadas antes de ampliar consultas.
- `manifest.json`: hashes de entrada y salida; registra las peticiones de la primera ejecución. La repetición puede usar cero red sin invalidar ese recibo.

La comparación auxiliar sirve para buscar y excluir duplicados. La prioridad usa la forma escrita; las ocurrencias del headword normalizado del catálogo se cuentan por separado y se señala cuando difiere. Los textos originales y sus grafías permanecen intactos.

## Una revisión compartida con excepciones

Las decisiones viven fuera del lote: `editorial/pipeline-decisions.json`, inicialmente vacío. Usar un archivo nuevo por lote cuando haya decisiones de otro lote. El [ejemplo](../templates/learning/pipeline-decisions.example.json) muestra cómo copiar un ID y fingerprint desde `review-groups.json` y cómo excluir un elemento con su fingerprint de `review-items.json`.

Se admiten `accepted`, `rejected`, `deferred`. Aceptar requiere responsable, fecha, evidencia y resolución. Un grupo aceptado puede tener elementos rechazados o diferidos en `items`; esos overrides prevalecen. Revisar en grupo significa compartir una decisión de fuente y alcance; no declarar que todas las acepciones o conexiones de un poema fueron verificadas.

```bash
.venv/bin/python -m nahuatl_local.editorial_pipeline assemble \
  --batch reports/editorial-pipeline/mi-lote-001 \
  --decisions editorial/decisiones-mi-lote-001.json \
  --output editorial/lote-revisado-001.json
```

Si preparaste el lote con `--catalog` o `--lessons`, pasar esos mismos argumentos a `assemble`. El ensamblador rechaza fingerprints obsoletos, archivos alterados, cambios del catálogo/lecciones/corpus/reglas, dependencias no aceptadas, IDs ya existentes y permisos de entrenamiento. Por ejemplo, aceptar un apoyo visual que depende de una nueva entrada requiere aceptar también esa entrada. No produce un lote vacío.

`assemble` crea un archivo revisable; no importa nada. Para usar el cotejo automático sin el comando completo:

```bash
.venv/bin/python -m nahuatl_local.editorial_pipeline verify \
  --batch reports/editorial-pipeline/mi-lote-001 \
  --output editorial/cotejo-mi-lote-001.json
```

Usar ese JSON en `assemble --decisions` acepta únicamente los elementos que pasaron las comprobaciones. El responsable queda identificado como **script de cotejo literal**, con `review_method=automated_source_comparison`, `primary_review=false` y `linguistic_certification=false`. No se simula un revisor humano. Las excepciones diferidas prevalecen sobre los grupos aceptados. Una caché modificada o ausente difiere la entrada y los apoyos que dependan de ella.

Para publicar el JSON ensamblado:

```bash
.venv/bin/python -m nahuatl_local.editorial_pipeline publish \
  --batch reports/editorial-pipeline/mi-lote-001 \
  --bundle editorial/lote-revisado-001.json \
  --release-id mi-lote-001
```

`--db` selecciona otra base; por defecto usa `data/community/voces.sqlite3`. `--lessons` permite cotejar el mismo archivo de lecciones empleado al preparar/ensamblar un lote personalizado. La publicación verifica el lote, sus aceptaciones, texto de las fuentes, originales, reglas y dependencias locales. No sustituye fichas ya existentes. Guarda `data/backups/voces-before-ID.sqlite3` (0600), `reports/publication-ID.json`, `corpus/editorial-ID.json` y su hash en `corpus/editorial-releases.json`. Un bloqueo serializa publicaciones; un intento interrumpido después de importar puede terminar su registro al repetirlo, si el respaldo y las fichas siguen intactos.

El importador genérico de la plataforma sigue disponible para aportaciones locales, pero no registra por sí solo una publicación distribuida. El siguiente `prepare`/`run` excluye lo ya incorporado usando el catálogo distribuido actualizado; `--catalog` permite partir de otra instantánea pública. No hay actualización del LLM ni movimiento de reservas a entrenamiento.

## Primera publicación comprobada

[Informe batch-007-v9](../reports/PIPELINE_PUBLICACION_2026-09-30.md): se incorporaron 50 acepciones, sus 50 formas y 39 apoyos visuales contextuales tras cotejo automático de alcance limitado. Se preservaron las 1.178 entidades previas y las tablas privadas. El catálogo actual tiene 1.317 entidades: 575 acepciones, 578 formas y 140 fichas glíficas. Hay 139 acepciones con imagen y 436 pendientes de evidencia; las imágenes siguen siendo 24 referencias documentales distintas.

La [preparación batch-007](../reports/editorial-pipeline/batch-007/README.md) conserva el recibo original de las ocho consultas agrupadas: 1.432 filas, 374 entradas elegibles, 50 seleccionadas. La primera página del diccionario conserva las 24 palabras representativas; el resto sigue el alfabeto náhuatl. No se modificaron los 12 pasajes ni sus lecciones.

[Siguiente lote batch-009-v11](../reports/editorial-pipeline/batch-009-v11/README.md): 50 entradas, 4 referencias contextuales, 100 concordancias y paquetes de las seis lecciones / 36 tareas. Está cotejado y ensamblado, **sin publicar**. Excluidas las formas ya incorporadas, las mismas fuentes ofrecen 322 entradas elegibles, 50 seleccionadas y 272 diferidas por límite. Su preparación y cotejo usaron cero red y cero LLM.

La [suite completa](../reports/tests-pipeline-release-full-2026-09-30.txt) ejecutó 175 pruebas: OK, con una falla esperada previamente registrada. Incluye las ocho pruebas de preparación/ensamblado y siete de cotejo/publicación: caché alterada, alcance declarado, preservación de perfiles y ediciones, nueva instalación, integridad de hashes, repetición y recuperación tras interrupción. Las aceptaciones sintéticas solo existen en bases/carpetas temporales. [Pruebas de interfaz](../reports/platform-ui-pipeline-release-2026-09-30.txt).


La ampliación educativa lecturas-002 cambió el hash de las lecciones. La preparación histórica batch-008-v10 se conserva pero su ensamblado quedó obsoleto; batch-009-v11 la sustituye con los paquetes actuales. El mecanismo rechaza la evidencia vieja en lugar de aplicarla silenciosamente. Para añadir recorridos con pasajes seleccionados y claves exactas, usar el [ensamblador de lecturas](LECTURAS_PIPELINE.md).


La mejora de lectura y comprensión del 7 de octubre cambió otra vez el hash de `corpus/learning-v1.json`. `batch-009-v11` se conserva como preparación histórica; no publicarlo contra la selección actual. Los ejemplos de comandos usan un ID nuevo (`batch-010-v12`), todavía sin preparar.

## Diccionario pictográfico · Amoxcalli

La consulta **Glifos** añade un índice documental separado del léxico didáctico: apariciones, zonas, elementos y valores por contexto. No convierte referencias temáticas previas en componentes ni añade sus datos al entrenamiento. [Modelo, lote piloto y comandos de ampliación](DICCIONARIO_PICTOGRAFICO.md). El nombre visible es Amoxcalli; las claves técnicas antiguas conservan compatibilidad y progreso.
