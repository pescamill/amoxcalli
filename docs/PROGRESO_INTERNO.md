# Estado interno de Scriptorium

Actualización: 30 de septiembre de 2026. Este documento es el punto de continuación del proyecto; los informes fechados conservan sus resultados históricos.

## Dirección acordada

El objetivo principal es aprender náhuatl mediante ejemplos. La primera ruta es náhuatl clásico (`nci`). El diccionario asocia palabras con glifos documentados de las fuentes ya registradas; no usa ilustraciones generadas. El LLM se conserva como línea de experimentación visible, con resultados y límites explicados.

## Iteración educativa · primer ciclo flor realizado

El [plan](LEARNING_ITERATION_PLAN.md), la [plantilla](../templates/learning/LESSON_TEMPLATE.md) y el [inventario](../reports/learning-audit/inventory.md) organizan un paquete activo y como máximo dos decisiones compartidas. Se ejecutó flor v2: cuicatl tiene entrada exacta de Molina/GDN; Cacahuaxochitl tiene entrada propia y referencia nominal explícita. Se conservaron los 12 originales y las otras dos lecciones. NIQUITTA y xochitli se muestran como relaciones pendientes, sin crear fichas que oculten ese vacío. El ejercicio final recupera xochitli exactamente.

Estado actual después de lecturas-002: 6 lecciones, 24 ejemplos de 6 obras y 12 acepciones objetivo; 12/12 con imagen y 0/12 con contexto primario declarado. Faltan fichas exactas de NIQUITTA, xochitli y tlacuilolcalli. Hay 36 tareas actuales: 1 resuelta editorialmente, 4 bloqueadas y 31 abiertas, más 2 resoluciones históricas con su evidencia original. Las decisiones de Codex están identificadas como revisión editorial/técnica, sin certificación lingüística. Evidencia cambiada reabre la tarea; el script no sobrescribe decisiones.

[Informe del ciclo](../reports/FLOR_CICLO_2026-09-30.md). [Ensayo preparado, no realizado](../editorial/flor-beginner-trial.md). Cotejar edición/páginas de los pasajes y relaciones lingüísticas sigue pendiente; no se atribuyen pruebas con personas a los checks de interfaz. 160 pruebas completas pasan con una falla esperada; seis bloques de interfaz pasan. Progreso por versión de lección conserva cielo y lugares. La extracción de búsquedas GDN usa caché, cero LLM y cero red al repetirla.

## Lecturas-002 · ampliación y aclaraciones

Se publicaron 3 recorridos: **agua-tierra**, **flores-cantos** y **aves**. Cada uno tiene 4 pasajes nuevos seleccionados del archivo clásico, claves cloze generadas desde la grafía original y notas de contexto explícitas. [Informe](../reports/LECTURAS_002_2026-09-30.md), [paquetes regenerados](../reports/learning-audit-lecturas-002/inventory.md), [receta](../configs/learning-expansion-2026-09-30.json). Las 12 selecciones y todas las claves anteriores permanecen iguales. Las aclaraciones de cielo/lugares usan `version=2`, `practice_version=1`; conservan la práctica guardada. Flor continúa en versión 2.

Se sustituyó «Una palabra. Un glifo. Un ejemplo.» por «Leer palabras en su contexto». La forma citada y la entrada de consulta tienen rótulos separados. Tlacuilolcalli→calli y tepetl en el registro traducido «ciudad» se identifican como consultas temáticas; la imagen no escribe el compuesto completo ni asigna una traducción universal. Cielo explica que la selección incluye un solo ejemplo con Luna; el corpus local etiquetado nci solo contiene un par cuyo español menciona luna. No se inventó otro ni se aplicó la acepción mes.

`nahuatl_local.lesson_builder` reúne selección, hashes, claves, validación de formas/portadas y publicación con respaldo. [Guía](LECTURAS_PIPELINE.md). Las recetas editoriales siguen explícitas: el script no decide morfología ni semántica por coincidencias. La interfaz cuenta los ejemplos dinámicamente y se comprobó también un recorrido de dos ejemplos. Lecturas, diccionario, imágenes y traducciones conservan revisión primaria/lingüística pendiente; no se registró un ensayo real con principiantes.

Verificación: [179 pruebas completas](../reports/tests-lectures-full-2026-09-30.txt), OK con una falla esperada; [checks finales de validación](../reports/tests-lectures-final-2026-09-30.txt); [interfaz](../reports/platform-ui-lectures-2026-09-30.txt), incluidos los tres nuevos recorridos, claves, conteos y ayuda temática. En el navegador real se observaron las 6 tarjetas, 24 ejemplos y el progreso previo de lugares (1/4) conservado.

## Pipeline editorial por lotes operativo y publicado

El usuario pidió un script que evite investigar entrada por entrada. `nahuatl_local.editorial_pipeline` ahora tiene `prepare`, `verify`, `assemble`, `publish` y `run`. [Guía y comandos](EDITORIAL_PIPELINE.md). `run --release-id NUEVO_ID` prepara, coteja las fuentes y ensambla un lote de hasta 50 entradas; `--apply` lo incorpora con respaldo privado y comprobación de preservación. Usa caché, cero LLM y cero red al repetir; `--fetch` obtiene únicamente páginas faltantes. Las decisiones agrupadas admiten excepciones por elemento. Evidencia obsoleta o dependencias cambiadas detienen el flujo.

**Publicado batch-007-v9:** 50 acepciones, sus 50 formas y 39 referencias contextuales (139 entidades). El cotejo automático verificó texto literal de Molina/GDN, imágenes/lecturas/créditos originales y coocurrencias en los pares archivados; no certificó semántica ni cotejo primario. Las fichas mantienen revisión pendiente y `rights.training=false`. [Informe](../reports/PIPELINE_PUBLICACION_2026-09-30.md), [preservación](../reports/publication-batch-007-v9.json), [registro distribuido](../corpus/editorial-releases.json). Las 1.178 fichas previas y todas las tablas de aportaciones se conservaron. Las nuevas instalaciones cargan el lote; la migración no reemplaza ediciones locales. Repetir el mismo ID no duplica registros.

**Lote histórico batch-008-v10 preparado, sin publicar:** 50 entradas, 4 referencias, 100 concordancias, paquetes de las 3 lecciones y 26 tareas (1 resuelta, 4 bloqueadas, 21 abiertas). Se reutilizaron las ocho páginas cacheadas: 322 entradas elegibles, 50 seleccionadas, 272 diferidas por límite. Cero red y LLM. [Paquete](../reports/editorial-pipeline/batch-008-v10/README.md); aceptación automatizada de alcance limitado en `editorial/batch-008-v10-source-check.json`. Sus hashes de lecciones quedaron obsoletos después de lecturas-002: no publicarlo. Se preparó **batch-009-v11**, también con 50 entradas y 4 referencias, 100 concordancias y los paquetes actuales de 6 lecturas / 36 tareas, con cero red/LLM. Continuar con `run --release-id batch-009-v11 --apply`.

Los originales de Axolotl y las lecciones no se reescriben; las concordancias y las propuestas de anotaciones no crean lecciones ni respuestas certificadas. Las decisiones humanas de `editorial/lesson-decisions.json` permanecen intactas. Cotejo primario, explicación de formas y ensayos con principiantes siguen pendientes. Los prototipos batch-001 a batch-006 y la preparación batch-007 conservan su estado histórico.

Verificación: 175 pruebas Python, OK con una falla esperada preexistente. [Suite](../reports/tests-pipeline-release-full-2026-09-30.txt). Las pruebas específicas verifican caché alterada, alcance del cotejo, publicación, ediciones/perfiles, instalación nueva, integridad del registro y recuperación tras una interrupción. El navegador real muestra 575 entradas y 139 con imagen, con las 24 palabras representativas en la primera página.

## Implementado

- Aprender: 6 lecturas, 24 ejemplos de 6 obras, ayuda al pulsar palabras, traducción ocultable, ejercicios con claves locales y retroalimentación.
- Leer: los mismos fragmentos con transcripción, traducción y procedencia de origen.
- Diccionario: 575 acepciones / entradas y 578 formas: 26 curadas + 549 transcripciones automáticas de Molina/GDN. Contiene 140 referencias glíficas y 139 entradas con imagen documental (24 imágenes distintas). La primera página conserva las 24 palabras representativas en el orden pedido, todas con referencia visual guardada; después aparecen las otras 551 en orden alfabético por forma náhuatl, 48 por página. Las referencias relacionadas muestran su alcance: significado, referente de la definición o coocurrencia exacta en un ejemplo clásico; no equivalen a escribir la palabra.
- Mis palabras: guardado y repaso; almacenamiento `scriptorium-study-v1` en el navegador y origen actual. No se sincroniza entre dispositivos.
- Laboratorio: tres pestañas, Probar / Datos de entrenamiento / Modelo y progreso. La búsqueda con fuente es la opción inicial; modelo y reglas son métodos separados. La antigua opción «Añadir pasajes» ahora explica el contexto RAG y muestra los ejemplos antes de generar. El visor bilingüe presenta los 650 pares recorridos y diferencia preparación histórica/actual/reservas. Permite proponer pares manualmente o por CSV, con perfil, fuente y permisos; permanecen privados hasta revisión y exportación.
- Archivo completo: 16.111 pares, 33 obras identificadas; fuentes, fichas textuales y herramientas editoriales se conservan. Voces vive en `/aportar`, con consentimiento separado y revisión.

El catálogo tiene 1.317 entidades: 575 acepciones / entradas, 578 formas, 140 glifos, 20 fuentes, 3 textos y 1 nota. El lote flor v8 añadió 5 entidades conservando exactamente las 1.173 previas y todas las tablas de aportaciones; respaldo privado 0600 en `data/backups/voces-before-flor-v8.sqlite3`, evidencia en `reports/data-preservation-flor-v8.json`. El lote v7 añadió 79 entidades sin alterar ninguna de las 1.094 fichas previas, sus versiones/fechas ni perfiles/aportaciones. Respaldo privado: `data/backups/voces-before-glyph-v7.sqlite3` (0600); comprobación en `reports/data-preservation-v7.json`. La migración v6 añade 998 entidades sin sustituir ediciones locales. El respaldo privado previo al lote es `data/backups/voces-before-gdn-v6.sqlite3` (0600). Se verificó que los 96 registros anteriores, sus versiones y fechas, los perfiles y las aportaciones se conservaron exactamente. El CSV original de Axolotl tampoco cambió.

## Asociación glífica por script · v7

El usuario pidió automatizar este trabajo con un script y autorizó componentes o referencias relacionadas con evidencia, siempre distinguiéndolas de la palabra completa. `nahuatl_local.glyph_linker` procesa una vez las fichas locales y el archivo clásico; no consulta internet ni usa el LLM. El lote se reproduce en unos 0,35 s con JSON idéntico. Las coincidencias usan palabras completas de la definición o tokens exactos de la paleografía en un pasaje, conservando el original. No usa letras compartidas para inventar componentes o fonogramas. La grafía normalizada de GDN no sustituye a la forma paleográfica al buscar el ejemplo.

La cobertura histórica v7 es 99 / 523. Las otras 424 quedan enumeradas en `reports/glyph-coverage-v7.json`; **el requisito de una referencia para todas las entradas todavía no está cumplido**. Para aumentarla hace falta ampliar el inventario documental de referencias, no más inferencia. Los vínculos de contexto son ayudas de lectura, no glifos atribuidos a esas palabras. El registro de reglas está en `corpus/glyph-link-rules-v7.json`; el lote validado en `corpus/glyph-associations-v7.json`. Nuevos referentes de madera y ver: Tlecuauh (MH487r) y Tlachia (MH716r), vía el VLA ya registrado; se identifica su documento primario, Matrícula de Huexotzinco. Para ihuan se muestra el ejemplo clásico «in Tonatiuh ihuan in Metztli.» con la referencia de metztli; se aclara que no escribe ihuan.

Verificación: 153 pruebas Python pasan (1 fallo esperado de la funcionalidad ortográfica desactivada), seis bloques de integración DOM/HTTP pasan; primera página y evidencia de ihuan comprobadas en navegador. Informes fechados en `reports/*glifos-2026-09-30.txt`.

## LLM: qué se conserva

Qwen3-0.6B + LoRA, 1.146.880 parámetros entrenables. Adaptador seleccionado por defecto: `outputs/continued-unseen/run/best`. Base, adaptador y dependencias están disponibles en este equipo. La carga de pesos ocurre al pedir generación; consultar el laboratorio no carga el modelo.

Los pesos corresponden al piloto de 400 pasos y a una continuación de 250 pasos, cuyo estado registrado es `paused_budget`. No hubo nuevos entrenamientos durante la implementación de aprendizaje, glifos, laboratorio, visor bilingüe o ampliación automática del diccionario. Los pesos no se actualizaron con el diccionario ni con palabras guardadas.

En aquella continuación: NLL 3,5783 → 3,5302 sobre 128 ejemplos; chrF++ 22,58 → 27,96 sobre 12 frases de validación. La repetición media de trigramas pasó de 0 a 0,028. Son medidas exploratorias sobre datos anteriores, sin revisión lingüística; chrF++ no es porcentaje de traducciones correctas.

`data/prepared` contiene hoy 5.462 pares (2.161/2.049/1.252), normalización `nah-ortho-1`. Sus hashes no coinciden con la corrida de los pesos existentes. Solo se reevaluó recuperación: 100 frases de validación, chrF++ 16,0123, sin generación. No comparar directamente esta cifra con las antiguas métricas del modelo. Ver [ESTADO_MODELO.md](ESTADO_MODELO.md) y [LABORATORIO.md](LABORATORIO.md).

## Extracción y referencia verificables

`nahuatl_local.dictionary_import` incorpora 499 entradas de las fuentes registradas mediante parser determinista: cero llamadas al LLM. Conserva paleografía y traducción histórica, grafía normalizada en otro campo, ID, enlace y hash de página. Excluye entradas generadas/compuestas, prefijos, remisiones y duplicados curados; falla antes de publicar si cambia el formato. Se repitió el lote desde caché con JSON idéntico byte por byte. No se trata de una revisión lingüística ni del diccionario completo.

Los tres JSONL históricos se recuperaron exactamente desde el CSV original y coinciden con los SHA256 de la corrida. `scripts/reconstruct-training-reference.py` recupera los 650 IDs recorridos del orden/cursor del checkpoint usando el tokenizador local; 1.759 filas eran admisibles de las 2.248 preparadas. La reproducción en otra carpeta coincidió con los tres splits y listas de IDs. No se usa la preparación actual para simular los datos de los pesos.

Las propuestas nuevas viven en `training_pair_proposals` de la base privada. Se bloquean duplicados y obras reservadas; aceptación desde terminal requiere revisión lingüística, permisos, responsable y motivo. Exportar → `curate` crea otra preparación preservando validación/prueba. No existe actualización automática de pesos ni uso del lote léxico con `rights.training=false`.

## Archivos para continuar

- `corpus/learning-v1.json`, `nahuatl_local/learning.py`, `nahuatl_local/platform_web/learning.js` y `learning.css`: recorrido educativo y diccionario.
- `corpus/glyph-lexicon-v5.json` y `glyph-source-images-v5.json`: palabras y asociaciones documentales.
- `nahuatl_local/laboratory.py`, `nahuatl_local/platform_web/laboratory.js` y `laboratory.css`: informes y presentación del laboratorio.
- `nahuatl_local/training_data.py`, `nahuatl_local/platform_web/training-data.js` y `data/training-reference/continued-unseen/`: visor bilingüe, propuestas privadas y referencia histórica.
- `nahuatl_local/dictionary_import.py`, `corpus/gdn-lexicon-v6.json` y `reports/dictionary-import-v6.json`: extracción automática y trazabilidad del lote.
- `nahuatl_local/platform.py`: servidor, API de aprendizaje, laboratorio y composición. `app.js` integra navegación y controles.
- [Entrega educativa](../reports/APRENDIZAJE_GLIFOS_2026-09-29.md): fuentes, migración y pruebas del piloto.

## Siguientes pasos

1. Revisar las 12 ayudas y ejercicios con una persona competente en náhuatl clásico; cotejar las referencias primarias y registrar responsable/versiones.
2. Probar las 6 lecturas con principiantes y corregir problemas observados de comprensión y navegación.
3. Ampliar las referencias documentales del script para las 436 entradas actualmente pendientes y cotejar el alcance de los vínculos publicados; cotejar folios y distinguir siempre la comparación contextual de una lectura glífica. Ampliar la extracción en lotes acotados después de verificar el formato; una imagen dentro de un topónimo no demuestra equivalencia universal.
4. Para el LLM: reunir una pequeña selección revisada y comparar recuperación, base y adaptador sobre la misma validación actual antes de otra corrida. Conservar prueba reservada y evitar duplicación de poemas entre antologías.
5. Incorporar más editores solo con un flujo claro de revisión y permisos; la aceptación actual sigue por terminal.

No aplicar automáticamente las 1.687 etiquetas `nci` propuestas en la auditoría de variantes: siguen pendientes de decisión documentada. No usar generaciones como respuestas correctas ni añadir fichas con `rights.training=false` al entrenamiento. Las anotaciones educativas y asociaciones glíficas continúan como propuestas editoriales, no como revisión especializada concluida.

## Arranque

`bash scripts/plataforma.sh` → `http://127.0.0.1:8766`. Aprender, leer, diccionario y laboratorio informativo funcionan sin ejecutar el LLM. Con base y dependencias instaladas, la generación local está disponible; `--disable-model` permite desactivarla. `bash scripts/iniciar.sh` sirve para preparar una instalación nueva.

La información del laboratorio se calcula a partir de informes y hashes en cada visita. El estado de disponibilidad del modelo se detecta al arrancar el servidor. Si se instalan dependencias o cambian pesos, reiniciar antes de comprobar ese estado.


## Comprobación de esta entrega

Suite de 149 pruebas: OK, con 1 fallo esperado de una regla ortográfica deshabilitada. Incluye integridad de la referencia histórica, consentimiento/privacidad de propuestas, exclusión de reservas, exportación revisada, parser de fuente y migración aditiva. La prueba DOM verifica las tres pestañas, 650 pares, paginación, propuestas y retiro en base temporal, CSV con comas/saltos de línea, 523 entradas y filtro por origen; sin errores JavaScript.

En navegador real se comprobó el visor bilingüe, paginación, preparación actual, explicación/vista previa de dos ejemplos para el modelo y ficha automática con paleografía, grafía normalizada separada y enlace GDN. La revisión móvil de Probar y Diccionario no mostró desbordamiento horizontal. Las comprobaciones técnicas no acreditan corrección lingüística. Informes: [suite](../reports/tests-datos-diccionario-2026-09-29.txt), [interfaz](../reports/platform-ui-datos-diccionario-2026-09-29.txt) y [entrega](../reports/DATOS_DICCIONARIO_2026-09-29.md).
