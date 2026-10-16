# Ampliar el léxico y la revisión compartida

El catálogo contiene 3.790 acepciones / entradas y 3.978 formas: 26 acepciones curadas, 549 entradas de transcripción automática de Molina/GDN y 3.215 lemas de Wiktionary (extracción automática, CC BY-SA; ver «Wiktionary · lote v12»). Contiene 140 fichas glíficas, 139 entradas con imagen y 24 imágenes documentales distintas; conserva las fichas anteriores. Los 16.111 pares de Axolotl son un archivo bilingüe separado. Un token frecuente de una oración no constituye por sí mismo un lema ni una traducción de diccionario.

El inventario exploratorio conserva **100 candidatos de concordancia** del corpus clásico ya etiquetado: [lexicon-candidates.json](../reports/lexicon-candidates.json) y [hoja de curación CSV](../reports/lexicon-candidates.csv). Cada grupo conserva grafías originales, frecuencia, obras, ejemplos bilingües y localizadores. No contiene acepciones españolas inventadas ni análisis morfológico automático. Los registros de la auditoría de variantes todavía pendientes se excluyen.

Los recuentos proceden de 5.993 filas clásicas originales; 2.431 grupos cumplen el mínimo de tres ocurrencias en dos obras. Se excluyeron 12 grafías de comparación de la semilla. La frecuencia hace aparecer partículas, préstamos y nombres propios junto a formas léxicas; un curador debe seleccionar cuáles merecen una entrada. Noventa y nueve de los 100 grupos contienen testimonios de obras reservadas, señalados expresamente.

```bash
.venv/bin/python -m nahuatl_local.lexicon_candidates \
  --output reports/mis-candidatos-lexicos.json \
  --csv reports/mis-candidatos-lexicos.csv
```

## De concordancia a entrada

1. Seleccionar una forma y cotejar sus testimonios con la edición primaria. Conservar página, folio o entrada de diccionario, autor y variante/localidad.
2. Identificar el lema y la categoría con un especialista; separar formas flexionadas, prefijos y homónimos sin asumir que comparten una acepción.
3. Escribir una definición en español y distinguir cada sentido. Registrar equivalencias y grafías alternativas mediante formas enlazadas.
4. Determinar permisos de cada fuente y registro. La existencia de un enlace bibliográfico o una etiqueta lingüística no habilita entrenamiento.
5. Importar el concepto, las fuentes y la forma con el contrato existente de `CorpusStore`, un revisor y un motivo de incorporación. Verificar enlaces e historial antes de publicar la ficha.

Los ejemplos llevan pertenencia al split preparado y la reserva por obra. Una fila excluida de la preparación puede pertenecer a una obra de validación/prueba; conservar esa relación evita recuperarla más tarde como un supuesto dato nuevo de entrenamiento.

Para el primer lote editorial conviene revisar entre 20 y 30 candidatos de pocas obras, con una persona competente en náhuatl clásico y otra responsable de edición/derechos. El inventario permanece separado de la base editorial hasta completar esa revisión. La selección de fuentes externas y modelos con restricciones no comerciales queda pendiente de la definición del uso educativo o comercial del proyecto.

## Qué ofrece ya la colaboración

La plataforma permite enviar propuestas de formas, textos y glifos, con fuente, localizador y permisos separados. El organizador acepta o rechaza desde terminal; la base guarda versiones y motivos. Las propuestas pendientes no se publican. Las exportaciones de entrenamiento exigen revisión y permisos de la forma y sus fuentes. Los sentidos y las nuevas fuentes se incorporan mediante importación estructurada.

## Qué hace falta para edición abierta

| Entrega | Comportamiento verificable |
|---|---|
| Cuentas recuperables y roles | Autor, revisor y administrador con acceso separado; los visitantes no pueden aprobar |
| Cola editorial en la web | Fuente y cambios lado a lado; motivo obligatorio al aceptar, rechazar o solicitar correcciones |
| Revisión compartida | Declarar responsable lingüístico y de derechos; impedir autoaprobación; conservar desacuerdos |
| Historial y reversión | Mostrar versión, responsable y motivo; restaurar una versión sin borrar la trazabilidad |
| Derechos por obra | Conservar titular, permiso, alcance, evidencia y fecha; distinguir consulta, redistribución y entrenamiento |
| Operación institucional | Respaldos probados, recuperación, límites de almacenamiento y política de retiro |

Para la presentación institucional se puede demostrar ahora la búsqueda del archivo, las fichas con fuentes, los glifos, una propuesta y su revisión local. El piloto todavía requiere esas entregas antes de abrir una instalación pública con varios revisores. Las voces y las variedades contemporáneas deben tener participación y revisión de sus comunidades; no se sustituyen por inferencias desde el corpus clásico.


## Ampliación basada en las fuentes registradas

El lote `corpus/glyph-lexicon-v5.json` incorpora doce acepciones seleccionadas por su evidencia léxica y visual, con referencias a fichas consultadas el 29 de septiembre de 2026. Este lote es independiente del inventario de frecuencia: no importa sus cien tokens como lemas. La condición `catalog_checked` declara consulta de una ficha secundaria; no equivale a aprobación de una persona especialista ni a cotejo del códice.

Las imágenes se vinculan al sentido y al contexto del documento, con clasificación explícita cuando la ficha identifica un elemento, glifo simple o iconografía. Un vínculo puede tener varios testimonios, y un testimonio del Mendoza no reemplaza otro del Xólotl. La siguiente tarea editorial es cotejar esos vínculos y las doce ayudas del piloto de lectura, registrando correcciones y responsables. Las imágenes y las nuevas entradas continúan con `rights.training=false`.


## Extracción automática GDN / Molina 2 · lote v6

`nahuatl_local.dictionary_import` extrae campos estructurados del [Gran Diccionario Náhuatl de la UNAM](https://gdn.iib.unam.mx/), fuente ya registrada. No utiliza LLM ni OCR. De 1.400 registros consultados incorporó 499 entradas seguras (998 entidades), excluyendo compuestos o entradas generadas, prefijos/puntuación, remisiones y formas ya curadas. Es un lote limitado, no el diccionario completo.

```bash
.venv/bin/python -m nahuatl_local.dictionary_import --limit 600
```

Las páginas quedan en caché local; repetir el lote produce el mismo JSON sin red. `--letters`, `--per-letter` y `--limit` permiten ampliar la extracción. Para un lote nuevo usa otro `--output` y `--report`, valida el resultado y regístralo como migración aditiva; la migración instalada reconoce `corpus/gdn-lexicon-v6.json`. No ejecuta entrenamiento ni programación periódica.

El parser conserva la paleografía y traducción histórica exactamente como texto de la ficha; decodifica los escapes de transporte y entidades HTML. La grafía normalizada del catálogo se guarda en `catalog_normalized`, separada del testimonio. No moderniza el español ni divide acepciones automáticamente. Cada entrada enlaza `/contexto/{id}` y conserva ID, URL de consulta y SHA256 de la página. Si cambia el formato, la extracción se detiene antes de publicar el lote. La validación del contrato precede a la escritura.

La migración añade IDs nuevos sin sustituir fichas editadas. El filtro «Origen» distingue transcripción automática y selección editorial; el diccionario reserva su primera página para las 24 palabras representativas; el resto se ordena por la forma náhuatl, 48 fichas por página. Las asociaciones y sus pendientes se gestionan por el script v7 descrito abajo. `catalog_checked` significa consulta del catálogo, no cotejo primario ni revisión especializada. `rights.training=false` evita usarlas automáticamente para entrenamiento.


## Enlaces visuales deterministas · v7

```bash
.venv/bin/python -m nahuatl_local.glyph_linker
```

Lee las referencias locales y los pasajes clásicos en una sola pasada. No usa LLM, embeddings, OCR ni red; repetir produce el mismo lote en aproximadamente 0,35 s. Valida antes de escribir `corpus/glyph-associations-v7.json`; la migración agrega IDs nuevos y conserva las ediciones locales. El generador no abre la base de perfiles: valida en SQLite temporal. El lote instalado se importa al iniciar `CorpusStore`; reinicia el servidor después de regenerar. Para modificar una asociación ya publicada usa la edición versionada del catálogo; cambiar el JSON no sustituye automáticamente una ficha local.

`corpus/glyph-link-rules-v7.json` reúne las 24 acepciones de portada y un pequeño inventario de referentes documentados. Se admiten tres relaciones:

- `related_meaning`: comparación de significado registrada explícitamente, como itta / Tlachia o madera dentro de Tlecuauh. Conserva la lectura real del glifo y su fuente.
- `definition_reference`: una palabra completa de la definición histórica menciona un referente del inventario; se conserva la definición como evidencia. No se infiere que sea un componente de la forma náhuatl.
- `passage_reference`: coocurrencia exacta de la forma paleográfica y del referente en un pasaje `nci`, con el referente también en español. Conserva ID, fila, ambos textos, documento, URL y hash. No demuestra equivalencia ni segmentación de la palabra; los documentos del glifo y del pasaje son distintos.

Los vínculos de definición y ejemplo son ayudas contextuales, **no componentes glíficos atribuidos a la entrada**. No se admiten asociaciones por letras compartidas o imágenes genéricas. Si no hay referencia, queda pendiente. Resultado histórico de v7: 99 de 523 entradas con imagen; 424 pendientes en [glyph-coverage-v7.json](../reports/glyph-coverage-v7.json). Todavía no se cumple la cobertura total pedida. Todos los vínculos nuevos tienen `rights.training=false`; las dependencias a forma, glifo original y fuentes se guardan en `corpus_links`, de modo que retirar una dependencia también oculta el vínculo público. Las imágenes abren directamente la ficha documental.

Para ampliar la cobertura, añade referentes y términos precisos al inventario con fuente, folio, crédito y alcance explícitos; ejecuta el mismo script y revisa el informe. No hace falta investigar cada palabra con el LLM. La importación preservó exactamente las 1.094 entidades anteriores.


## Publicación por lotes · batch-007-v9

Se añadieron 50 acepciones, sus 50 formas y 39 referencias contextuales mediante cotejo literal automático de GDN y de los pares/imágenes archivados. No se declara revisión lingüística ni lectura glífica completa. Cada referencia conserva su tipo, nota, imagen, crédito, evidencia y dependencias. Resultado actual: 139 de 575 entradas con imagen; 436 pendientes. El [pipeline](EDITORIAL_PIPELINE.md) publica lotes con respaldo, hashes y preservación de originales y aportaciones. La transcripción paleográfica y la normalización del catálogo siguen en campos separados; no se asignan acepciones por frecuencia ni por letras compartidas.

## Diccionario pictográfico · Amoxcalli

La consulta **Glifos** añade un índice documental separado del léxico didáctico: apariciones, zonas, elementos y valores por contexto. No convierte referencias temáticas previas en componentes ni añade sus datos al entrenamiento. [Modelo, lote piloto y comandos de ampliación](DICCIONARIO_PICTOGRAFICO.md). El nombre visible es Amoxcalli; las claves técnicas antiguas conservan compatibilidad y progreso.


## Wiktionary · lote v12

`corpus/wiktionary-lexicon-v12.json` añade 3.215 lemas de náhuatl clásico (2.031 con acepciones en español, 1.184 en inglés, marcadas con `gloss_language`) y 3.400 formas, desde los extractos wiktextract de kaikki.org. Cada registro enlaza la revisión de su página y lleva licencia CC BY-SA 4.0, atribución y `training=false`. Estado «extracción automática»: sin cotejo primario ni revisión lingüística. No entran los lemas que ya tenían forma en el catálogo (236), los préstamos del español y nombres extranjeros (230), locuciones, afijos y reconstrucciones. La importación preservó las 1.317 entidades anteriores. Procedimiento, deduplicación y consecuencias de share-alike: [FUENTES.md](FUENTES.md#wiktionary-y-share-alike).

El analizador usa estas entradas con menos peso: una raíz apoyada solo en Wiktionary vale 3 puntos menos que una con fuente lexicográfica (`morphology.SECONDARY_PENALTY`), de modo que *nocal* sigue siendo *no-cal* y no *n-ohcal* («calle»). En un compuesto, cada parte necesita su propio apoyo: una parte solo de Wiktionary resta lo mismo (*iehecatzin* es *i-eheca-tzin*, no *eecatl* + *tzintli*). El valor se eligió mirando las particiones dev y test del conjunto de referencia (con dev sola se habría elegido 5): la partición test ya no es ciega para esta decisión.
