# Amoxcalli: aprender, consultar y aportar

Actualización: 2026-09-29. Español primero. Python y SQLite; no necesita APIs, PyTorch ni un LLM para consultar o aportar.

## Una plataforma, un corpus

Voces deja de ser una app desconectada. La entrada principal de Amoxcalli reúne Aprender, Leer, Diccionario, Mis palabras y Laboratorio. Archivo completo, fichas textuales y fuentes están en «Archivo y herramientas». La escritura, grabación y revisión comunitaria de Voces viven en `/aportar`. Comparten servidor, cookies de sesión y `data/community/voces.sqlite3`.

La unidad léxica es una **acepción**, no una traducción universal. «Árbol» y «madera» tienen IDs distintos; «luna» y «mes» también. Cada acepción puede tener numerosas formas por variante, localidad, época y convención de escritura. `quauitl` y `cuahuitl` muestran una relación ortográfica heredada; no se hacen pasar por dos dialectos modernos.

```mermaid
flowchart TD
  A["Acepción en español"] --> B["Formas por variante y época"]
  A --> C["Textos y referencias glíficas"]
  B --> D["Evidencia: fuente y localizador"]
  C --> D
  D --> E["Obra primaria, edición y estudio"]
  F["Voces y extracción móvil"] --> G["Propuestas y revisión"]
  G --> B
  G --> C
  B --> H["Consulta y exportación"]
  C --> H
  H --> I["Entrenamiento opcional con permisos"]
```

## Arranque y actualización

```bash
bash scripts/plataforma.sh
```

Abre http://127.0.0.1:8766. `bash scripts/voces.sh` es un alias del mismo arranque. Para otra ubicación de la base:

```bash
python3 -m nahuatl_local.platform --db /ruta/mi-corpus.sqlite3 serve
```

Antes de actualizar una instalación con datos, detén el servidor y copia `data/community/` a un respaldo privado. Conserva tu carpeta `data`; no está incluida en el ZIP. La migración crea únicamente tablas `corpus_*`, no sobrescribe las tablas de Voces ni modifica pesos. La semilla se importa una vez; los registros tienen ID y versión. Los datos de pruebas están en directorios temporales y no se distribuyen.

Se recuperó la fuente de Amoxcalli en el commit `3e8a7a67f995f92858519c6cffe15e74d0e7c794`. Se portaron sus 17 registros y sus reglas limitadas de composición. `corpus/scriptorium-legacy.json` conserva la procedencia; `corpus/seed.json` es el corpus normalizado. No se trasladó la dependencia del cliente OpenAI. El alojamiento anterior permanece en su versión previa; este paquete es la versión local integrada.

## Catálogo instalado (semilla y migraciones)

| Entidad | Cantidad | Estado |
|---|---:|---|
| Acepciones / entradas | 575 | 26 curadas + 549 transcripciones automáticas de Molina/GDN; traducción histórica intacta |
| Formas | 578 | Paleografía de fuente; grafía normalizada del catálogo en campo separado |
| Textos | 3 | Dos fragmentos heredados y una referencia sin transcripción |
| Referencias glíficas | 140 | 139 entradas con imagen; 24 imágenes distintas, contexto, folio y atribución |
| Fuentes | 20 | Primarias, ediciones, investigación, catálogos y testimonio comunitario |
| Nota gramatical | 1 | Regla limitada; no certifica oraciones nuevas |

«Aún no hay glifos vinculados a esta acepción» señala una tarea pendiente de catalogación local. No afirma que el glifo no exista. Cada ficha ofrece acceso al Visual Lexicon of Aztec Hieroglyphs. Los glifos vinculados distinguen la referencia al catálogo del cotejo primario y de la interpretación de la acepción. La misma forma puede pertenecer a distintas acepciones. Un elemento glífico dentro de un topónimo no equivale automáticamente a una palabra aislada ni a todas sus realizaciones contemporáneas.

UNAM, INALI e INAH tienen prioridad de navegación, junto con recursos complementarios de Oregon y Getty. Las nuevas fichas consultadas incluyen Tlachia, el diccionario de Thouvenot basado en Molina, el artículo de Silva Galeana y Silva Cruz (2021) y la guía de Thouvenot (2023). No se copian libros completos ni se infiere que «acceso abierto» autorice cualquier uso de entrenamiento.

La colección inicial **todavía no es un corpus exhaustivo ni una traducción fiable**. Hay formas sin cotejo primario y grandes vacíos dialectales. La estructura permite llenarlos mediante importaciones y revisión documentada.

## Proponer desde computadora o teléfono

1. Abre Voces, elige tu variante o autodenominación y crea un seudónimo. Se conserva el perfil existente si ya lo tenías.
2. Desde una acepción, pulsa «Aportar una forma o evidencia», o entra en Aportar.
3. Elige forma léxica, fragmento o glifo. Conserva la escritura del documento y añade fuente y página/folio/entrada. En testimonios propios, identifica una sesión; evita datos personales.
4. Declara por separado revisión, consulta y entrenamiento. En la época contemporánea se conserva una copia de la variante del perfil. La clasificación histórica sigue siendo una propuesta por revisar.
5. Envía. La propuesta no aparece en el corpus público hasta ser aceptada y tener permiso de consulta. Puede retirarse desde «Mis aportaciones al corpus».

La voz sigue en Voces: grabación, carga, escucha y revisión por variante, con los permisos originales. Las respuestas antiguas de Voces **no se hacen públicas automáticamente**: su consentimiento original solo cubre el proyecto. Los datos de voz no se promocionan al catálogo público por una mera votación. Sus exportaciones revisadas siguen disponibles mediante la CLI de comunidad.

El extractor actual permite transcripción **manual**; no realiza OCR, segmentación automática de facsímiles ni reconocimiento de voz. Se pueden añadir después como generadores de propuestas, conservando el documento de origen, el localizador y la corrección humana.

### Acceso desde tu teléfono en la misma red

En una red local de confianza, inicia con la IP local concreta de tu computadora:

```bash
bash scripts/plataforma.sh --host 192.168.1.25 --port 8766
```

Sustituye la IP por la tuya y abre `http://192.168.1.25:8766` desde el teléfono. Esto expone la consulta a dispositivos que puedan conectarse a ese servidor; úsalo para un piloto controlado. Los permisos de «consulta» significan visible a quienes accedan a esa instalación, no publicación automática en internet.

Para **grabar directamente con el micrófono desde otro dispositivo**, sirve el proyecto mediante un proxy HTTPS con certificado confiable para el teléfono:

```bash
bash scripts/plataforma.sh --host 127.0.0.1 --port 8766 --public-origin https://tu-dominio
```

Configura ese dominio en el proxy y pásalo como `Host`. HTTP local remoto permite usar los formularios y cargar un audio ya grabado, pero los navegadores suelen exigir un contexto seguro para capturar el micrófono. No hace falta una API de voz. La webapp incluye manifiesto de instalación para navegadores compatibles y pantalla de desconexión. No hay sincronización offline: consulta y envío requieren conexión al servidor. Guía: [WEBAPP.md](WEBAPP.md).

## Revisión: responsabilidad del organizador

La revisión que modifica el corpus se realiza desde terminal; no hay un botón de administrador accesible a cualquier visitante.

```bash
python3 -m nahuatl_local.platform queue
python3 -m nahuatl_local.platform review ID_DE_PROPUESTA \
  --decision accepted --reviewer 'Nombre o ID del revisor' \
  --reason 'Explicación del cotejo y de los permisos' --rights-checked
```

`--rights-checked` es una declaración del revisor: hay que revisar la fuente y los permisos, no solo marcarla. Para afirmar cotejo con una fuente primaria, añade `--primary-checked`, con una fuente registrada como primaria y una justificación concreta. En glifos, esto cambia el estado de «propuesto» a «documentado en este contexto». El programa valida la estructura de la declaración; **no puede comprobar que el revisor haya leído el original**.

Para rechazar usa `--decision rejected` y explica por qué. Las propuestas no se modifican silenciosamente: el autor puede retirar y enviar una corrección. Los desacuerdos y grafías alternativas se conservan en aportaciones separadas.

El retiro elimina el contenido del registro activo y su historial de contenido, conserva una marca de retiro y lo excluye de nuevas consultas y exportaciones. Si otros registros dependían de uno privado o retirado, dejan de mostrarse también. Los archivos ya exportados o los modelos ya entrenados no pueden deshacerse por ese mecanismo.

## Incorporar fuentes, estudios y nuevos conceptos

Ejemplo real adicional, incluido como plantilla, de un proyecto de investigación de la UNAM:

```bash
python3 -m nahuatl_local.platform import templates/corpus-import.json \
  --reviewer 'Tu nombre' --reason 'Registro bibliográfico del proyecto y revisión de su ficha'
```

El JSON raíz contiene `schema_version: 1` y `records`. Se admiten `source`, `sense`, `form`, `text`, `glyph`, `note`. Usa IDs estables y distintos. Una segunda importación que edita un ID necesita `expected_version` igual a su versión actual; el lote completo se rechaza si hay referencias rotas o conflictos. No se elimina el corpus anterior al importar.

| Entidad | Campos que dan sentido al registro |
|---|---|
| Fuente | Autor, título, fecha, institución, idioma, tipo, URL, derechos; `primary_source_id` si es una edición vinculada |
| Acepción | Lema español, definición, categoría, alias; separar polisemia |
| Forma | `sense_id`, `written`, época, variante, ortografía y relación de variación |
| Texto | Náhuatl, español si está disponible, transcripción o referencia sin texto, variante, época, acepciones relacionadas |
| Glifo | Acepción, lectura, contexto del compuesto, fuente primaria, folio y estado de propuesta/cotejo |
| Nota | Explicación o estudio con evidencias enlazadas |
| Evidencia | `source_id`, `locator`, estado y, si corresponde, `via_source_id`; quién y cuándo cotejó el original |

Todos los registros necesitan derechos de consulta y entrenamiento separados y estado de verificación. Las formas no se normalizan al guardar; solo se usa normalización auxiliar para buscar sin acentos. La comparación lingüística nunca se deduce de esa normalización.

Usa `corpus/seed.json` como ejemplo completo del contrato. El validador operativo está en `nahuatl_local/corpus.py`. Se mantienen versiones y motivos de cambios en SQLite. Es un esquema v1 extensible; faltan coordenadas de facsímil/IIIF, morfología detallada, relaciones etimológicas y revisión editorial múltiple.

## Exportar para investigación o para modelos

En la interfaz se exportan el corpus consultable, una ficha con fuentes y citas bibliográficas. Es una copia para investigación local: los derechos de cada registro siguen aplicando.

```bash
python3 -m nahuatl_local.platform export --purpose research --output corpus-investigacion.json
python3 -m nahuatl_local.platform export --purpose training --period modern --output entrenamiento-moderno.json
python3 -m nahuatl_local.platform export --purpose training --period historical --output entrenamiento-historico.json
```

No se sobrescribe un archivo existente. El exportador de entrenamiento exige: revisión registrada, permiso del registro y de sus fuentes, variante conocida, transcripción/forma válida y, en lo histórico, cotejo primario declarado. Excluye glifos y simples referencias sin texto como pares de traducción. La semilla inicial produce **cero pares habilitados para entrenar**; esto evita heredar permisos no demostrados de catálogos. Las aportaciones propias revisadas pueden habilitarse con sus consentimientos.

Los registros exportados conservan grupo de fuente y, para aportaciones nuevas, grupo seudónimo de hablante. `split` queda en `unassigned`: antes de entrenar se debe separar por obra/hablante, deduplicar, evaluar alineación y evitar contaminación entre conjuntos. No se escriben automáticamente los archivos que consume `autotrain`. Un entrenador futuro debe respetar estos campos y mantener corpus clásico y variantes contemporáneas separados.

## Modelo y revisión humana dentro del ecosistema

Actualización: el modelo se activa automáticamente cuando sus dependencias, base y adaptador están disponibles. `scripts/iniciar.sh` prepara todo. La búsqueda principal consulta el archivo completo, no sólo el léxico editorial. Consulta `ESTADO_MODELO.md` para los resultados reales de esta integración.

El laboratorio porta las reglas limitadas de Amoxcalli: palabra aislada, «veo + un objeto singular» y coordinación de dos sustantivos. Toda oración nueva se marca como propuesta. No cubre negación, otros tiempos o número por inferencia.

Para habilitar el modelo existente, instala y descarga primero sus dependencias como indica el README y arranca:

```bash
bash scripts/plataforma.sh --enable-model --adapter outputs/continued-unseen/run/best
```

La carga es perezosa y local. Se conserva el modelo, entrenamiento y evaluación previos; no se volvió a entrenar durante esta integración. Los splits de entrenamiento y sus comandos se conservan. El CSV íntegro de Axolotl ahora se consulta como archivo separado, con etiquetas y atribuciones de origen. Sus pasajes no se convierten automáticamente en fichas editoriales aprobadas ni en nuevos pares autorizados de entrenamiento.

La ficha de revisión exporta candidato, entrada y evidencias para evaluación humana. Las reglas locales no certifican fidelidad lingüística y no se conectan a servicios de evaluación.

## Ampliación recomendada

El siguiente trabajo es editorial: seleccionar una obra o una variante, registrar su edición y derechos, transcribir un conjunto pequeño con localizadores, pedir revisión a hablantes o especialistas y publicar únicamente las fichas autorizadas. Después se amplía la cobertura. La calidad del corpus beneficia simultáneamente al investigador, al lector y al modelo.

Para reuniones entre varias personas, queda pendiente un despliegue endurecido con cuentas recuperables, roles de revisor, límites de almacenamiento y respaldos administrados. El piloto actual usa sesiones locales de larga duración y no ofrece recuperación de cuenta. La interfaz no debe confundirse con una plataforma pública de producción.

## Actualización de referencias glíficas

El lote `corpus/glyph-links-v2.json` añade cuatro referencias consultadas en VLA (árbol, sol, luna y mes) y la fuente Códice Osuna. Se aplica al primer arranque de esta versión, también sobre bases existentes. Conserva los cinco vínculos anteriores y cualquier edición local con el mismo identificador; repetir el arranque no duplica registros. Total glífico anterior: 57 entidades, incluidas 9 referencias glíficas. No se ha importado el catálogo completo.

El lote `corpus/glyph-images-v4.json` enlaza (no copia) la imagen de cuatro glifos heredados de Amoxcalli —flor, agua, casa y árbol florido— desde sus fichas del Visual Lexicon of Aztec Hieroglyphs, con atribución visible a Bodleian Libraries, University of Oxford (MS. Arch. Selden. A. 1) y licencia CC BY-NC-SA 3.0 UK. La webapp las muestra mediante enlace directo (hotlink) con crédito y enlace de retorno; las fichas sin imagen mantienen su referencia; si falla un enlace externo, la interfaz conserva el acceso a la fuente. El relleno es idempotente: añade `image` e `image_credit` solo a glifos ya presentes y no sustituye ediciones locales.

## Archivo de consulta

`research.py` consulta el CSV íntegro de Axolotl conservando 16,111 pares y sus etiquetas. `/api/research` pagina y filtra; `/api/research/<id>` conserva una referencia estable dentro de la revisión fijada. La fuente editorial `src-axolotl` se añade con una migración que no sobrescribe modificaciones existentes. Este archivo no altera los splits del entrenamiento ni la publicación de aportaciones pendientes.

Las consultas con texto se ordenan con BM25 en español y náhuatl; los filtros y la paginación se aplican sobre los resultados. El campo náhuatl usa las reglas seguras de comparación de `nah-ortho-1`; el español conserva su tokenización. Los resultados muestran el texto original. La navegación sin consulta conserva el orden del archivo. La recuperación de contexto del laboratorio usa el mismo índice, limitada a náhuatl clásico y pasajes breves. Este índice completo no participa en el benchmark reservado, que utiliza solo `train.jsonl`.

La política CSP de Amoxcalli permite imágenes de `https://aztecglyphs.wired-humanities.org` para los cuatro enlaces aprobados. El servidor de Voces por separado mantiene imágenes locales. Scripts, conexiones y otros orígenes de imágenes conservan sus restricciones. Se comprobó la carga real de agua, casa, flor y árbol florido en el navegador, además del encabezado HTTP.

Las propuestas de clasificación del archivo están en `corpus/variant-proposals-v1.json`, pendientes de decisión; la ampliación de las acepciones y el trabajo necesario para una plataforma editorial compartida se describe en [LEXICO_GOBERNANZA.md](LEXICO_GOBERNANZA.md).


## Lectura guiada y diccionario visual · 29 de septiembre de 2026

`corpus/glyph-lexicon-v5.json` amplía el índice con doce acepciones de animales y naturaleza, trece formas (incluida eecatl como grafía aparte) y trece referencias visuales del Códice Mendoza. Reutiliza las fuentes registradas de Molina, Online Nahuatl Dictionary, Códice Mendoza y VLA. Cada palabra nueva tiene una imagen de fuente y contexto específico. Fuego se muestra como **iconografía**, según la clasificación de la ficha; la relación Ecatl/Ehecatl conserva la interpretación del catálogo. No se registra cotejo primario ni se conceden permisos de entrenamiento.

`corpus/glyph-source-images-v5.json` completa las imágenes de árbol, sol, luna y mes mediante una migración separada que conserva ediciones locales. Piedra recibe una referencia del Mendoza aparte de la ficha existente del Xólotl. Ver, y/con y madera siguen sin imagen glífica específica incorporada. La interfaz ofrece los enlaces al catálogo y al folio cuando está localizado. Las imágenes necesitan conexión a sus servidores externos; un fallo conserva la ficha y su enlace.

`corpus/learning-v1.json` selecciona 48 fragmentos de 10 obras, agrupados en 12 lecturas tras el lote del 7 de octubre. `/api/learning` conserva la fila de Axolotl y verifica su etiqueta nci, hash y correspondencia literal de las anotaciones. Las ayudas son editoriales y las claves se basan en el texto seleccionado; no se utiliza el LLM como corrector. La traducción y su cotejo siguen pendientes de revisión lingüística. Los glifos y los pasajes alfabéticos proceden de documentos distintos, enlazados por acepción; no se presenta una imagen como escritura de toda la frase.

El cuaderno y las lecturas guardan progreso en `localStorage` del navegador, separado de perfiles y aportaciones de Voces. Cambiar de navegador u origen crea otro cuaderno. Si no se permite almacenamiento, el repaso funciona durante la sesión con un aviso. La revisión de palabras se agenda a 1, 3, 7 y 14 días según lo que la persona marca como recordado; no acredita aprendizaje lingüístico.


## Laboratorio visible y continuidad interna

El Laboratorio (`#modelos`) explica la base Qwen y el adaptador LoRA, muestra curva NLL y resultados con sus informes, detecta cambios de hashes respecto a los datos actuales y ofrece controles de generación separados de las reglas y la búsqueda. No entrena al consultar ni incorpora automáticamente palabras o aportaciones. Detalles: [LABORATORIO.md](LABORATORIO.md). El punto de continuación del proyecto es [PROGRESO_INTERNO.md](PROGRESO_INTERNO.md).


El laboratorio ahora separa `#modelos/probar`, `#modelos/datos` y `#modelos/progreso`. `/api/training-data` pagina y busca pares de la referencia histórica o preparación actual. `/api/training-pairs` guarda propuestas privadas autenticadas; la exportación incluye solo aceptadas mediante revisión lingüística y de permisos. Se rechazan coincidencias con pares existentes y obras de evaluación. No hay entrenamiento desde estos endpoints.

La migración v6 incorpora 499 entradas de GDN/Molina mediante parser determinista, conservando los 96 registros anteriores íntegros. El paquete incluye exclusivamente `data/training-reference` dentro de `data/`; excluye perfiles, propuestas, audio, respaldos y caché de consultas.


### Diccionario: portada y vínculos v7

La página 1 conserva las 24 palabras representativas solicitadas, con referencia visual para cada una. Las otras 551 aparecen por orden alfabético de la forma náhuatl, 48 por página. Buscar o filtrar muestra coincidencias alfabéticas, sin reservar una página vacía. Las imágenes abren la ficha de origen; la evidencia de cada relación se ve en la entrada. Las relaciones de significado, definición y ejemplo no se presentan como escritura de la palabra. El script local `python -m nahuatl_local.glyph_linker` no usa modelo ni red; produce lote validado e informe de cobertura. Hay 139 entradas enlazadas y 436 pendientes de evidencia. Detalles: [LEXICO_GOBERNANZA.md](LEXICO_GOBERNANZA.md).


## Publicaciones editoriales por lotes

El [pipeline](EDITORIAL_PIPELINE.md) coteja fuentes cacheadas y publica lotes aditivos con respaldo y prueba de preservación. `corpus/editorial-releases.json` registra archivos versionados y sus hashes; las instalaciones nuevas y existentes los cargan sin sustituir ediciones locales. El lote batch-007-v9 añade 50 entradas, 50 formas y 39 referencias contextuales. La app tiene 1.317 entidades. No cambian los permisos de entrenamiento, los pesos ni las lecciones originales.


La ampliación lecturas-002 conserva las doce selecciones y claves previas, añade tres recorridos y aclara enlaces temáticos. `practice_version` distingue la edición de ejercicios de las aclaraciones de contenido; cielo/lugares conservan su práctica. El contador de ejemplos es dinámico. [Guía de recetas y publicación](LECTURAS_PIPELINE.md).

## Diccionario pictográfico · Amoxcalli

La consulta **Glifos** añade un índice documental separado del léxico didáctico: apariciones, zonas, elementos y valores por contexto. No convierte referencias temáticas previas en componentes ni añade sus datos al entrenamiento. [Modelo, lote piloto y comandos de ampliación](DICCIONARIO_PICTOGRAFICO.md). El nombre visible es Amoxcalli; las claves técnicas antiguas conservan compatibilidad y progreso.
