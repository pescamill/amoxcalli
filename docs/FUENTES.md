# Fuentes y decisiones de uso

Revisión: 16 de octubre de 2026 (fuentes abiertas añadidas; tabla original del 16 de septiembre). Prioridad: instituciones mexicanas, estudios y pares en español. No se mezclan variantes modernas por conveniencia de tamaño.

| Fuente | Función | Uso actual y límites |
|---|---|---|
| [Axolotl, UNAM](https://www.axolotl-corpus.mx/) | Corpus paralelo histórico y moderno | Filtrado de náhuatl clásico; alineación heredada, no verificada individualmente |
| [Descripción UNAM](https://www.dgcs.unam.mx/boletin/bdboletin/2017_134.html) | Contexto institucional | Referencia |
| [Artículo de Axolotl, LREC 2016](https://aclanthology.org/anthology-files/pdf/L/L16/L16-1666.pdf) | Metodología; Gutiérrez-Vasques, Sierra, Hernández Pompa | Citar al utilizar el corpus |
| [Comunidad Elotl](https://github.com/ElotlMX/py-elotl) | Distribución reproducible | Repositorio MPL-2.0; conservar licencia; auditoría por obra pendiente |
| [Gran Diccionario Náhuatl, UNAM](https://gdn.iib.unam.mx/) | Consulta lexicográfica y fuentes históricas | Referencia; no se descarga masivamente ni se presume licencia de entrenamiento |
| [Estudios de Cultura Náhuatl, UNAM](https://nahuatl.historicas.unam.mx/) | Filología, traducciones, ediciones y estudios en español | Referencia, excluida de entrenamiento automático |
| [Derechos de ECN](https://nahuatl.historicas.unam.mx/index.php/ecn/derechos_autor) | Licencias de artículos | CC BY-NC-SA en política actual; volúmenes 1–59 CC BY-NC-ND; revisar cada artículo. No equivalen a permiso abierto sin restricciones |
| [Wikcionario](https://es.wiktionary.org/wiki/Categor%C3%ADa:NCI:Lemas) y [Wiktionary](https://en.wiktionary.org/wiki/Category:Classical_Nahuatl_lemmas), vía [kaikki.org](https://kaikki.org/) | Lemas, acepciones (español o inglés, marcado) y formas de náhuatl clásico | CC BY-SA 4.0. Lote `corpus/wiktionary-lexicon-v12.json`: extracción automática, revisión por página, atribución por registro, `training=false`. Ver «Wiktionary y share-alike» |
| [Carochi, *Arte de la lengua mexicana* (1645), facsímil en Internet Archive](https://archive.org/details/artedelalenguam00caro) | Gramática histórica: cita de capítulo y folio | Dominio público. Solo notas breves redactadas por el proyecto (`corpus/grammar-notes-carochi-v1.json`); no se distribuye el OCR ni ediciones modernas |
| [Tlachia, UNAM](https://tlachia.iib.unam.mx/) | Láminas, glifos, elementos y lecturas | Enlaces e imágenes cargadas desde su sitio, con atribución; índice en `corpus/pictography/catalog.json`. Permiso de incorporación solicitado (borrador en `docs/permisos/`) |
| [Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B) | Base de 0.6B parámetros del laboratorio histórico (archivado en `experiments/llm/`, fuera de la aplicación) | Apache-2.0; no se afirma competencia acreditada en náhuatl clásico |
| [PEFT LoRA](https://huggingface.co/docs/peft/developer_guides/lora) | Adaptación de pesos (laboratorio histórico) | Entrenamiento local de matrices pequeñas; retirado de la aplicación |

Los glifos enlazados proceden del catálogo académico Visual Lexicon of Aztec Hieroglyphs (Oregon), como complemento secundario. Se conserva el contexto de sus elementos del Códice Mendoza: [flor, 10r](https://aztecglyphs.wired-humanities.org/content/xochitl-mdz10r), [agua, 51r](https://aztecglyphs.wired-humanities.org/content/atl-mdz51r-0), [casa, 13r](https://aztecglyphs.wired-humanities.org/content/calli-mdz13r). No se copian imágenes ni se interpreta que los glifos equivalgan directamente a cada palabra de una oración moderna.

Para un registro aprobado añadir: institución, autor, título, edición, año, variante, transcriptor, alineador, URL estable, localizador de página/folio, licencia exacta, permiso de redistribución, revisión lingüística y hash. La existencia de una URL no constituye verificación filológica.


## Fuentes abiertas · 16 de octubre de 2026

Decisión del 15 de octubre: ampliar primero con fuentes de dominio público o con licencia abierta, y pedir permiso al Gran Diccionario Náhuatl, a Tlachia y a los editores del Códice Florentino antes de incorporar más de ellos. Los borradores de esas solicitudes están en [docs/permisos/](permisos/) y **no se han enviado**.

### Wiktionary y share-alike

`python -m nahuatl_local.wiktionary_import --fetch` lee los extractos de wiktextract publicados en kaikki.org (receta con URL y SHA-256 en `editorial/wiktionary-nci-v12.json`; caché en `data/wiktionary-cache/`, fuera de git) y consulta la API de Wikimedia para fijar la revisión de cada página vigente en la fecha del volcado. Sin red, el mismo comando reproduce el lote byte a byte; `--check` lo comprueba. Cada registro lleva:

- lema (título de la página), acepciones con su idioma (`gloss_language`: `es` o `en`; las inglesas se muestran como tales, sin traducir) y formas flexionadas o alternativas;
- URL permanente de la revisión (`oldid`) y localizador con sección, revisión y volcado;
- `rights`: `license=CC BY-SA 4.0`, `share_alike=true`, atribución a los colaboradores de la página y `training=false`;
- `import_status=automatic_transcription`, `import_source=wiktionary` y verificación `inherited` («extracción automática», sin cotejo ni revisión especializada).

Deduplicación: un lema cuya clave fonémica ya tiene una forma en el catálogo (Molina/GDN, curadas o publicaciones editoriales) no entra; el registro previo no se toca y el informe `reports/wiktionary-import-v12.json` lista cada duplicado con la ficha existente. Entre extractos se prefiere el español (sección clásica, luego grafía normalizada) al inglés. Se excluyen locuciones, afijos, entradas sin glosa y reconstrucciones no atestiguadas. Antes de escribir, el lote se importa en una base temporal y se comprueba que todos los registros previos quedan idénticos; `tests/test_open_sources.py` repite la comprobación.

**Implicación share-alike.** El lote es una adaptación de Wiktionary y se distribuye bajo **CC BY-SA 4.0**, no bajo la licencia MIT del código:

- Quien redistribuya `corpus/wiktionary-lexicon-v12.json`, o las fichas que contiene dentro de `corpus/lexicon-catalog.json` o de una exportación, debe conservar la atribución (enlace a la revisión de cada página), indicar la licencia y no imponer condiciones adicionales.
- Una corrección o ampliación de esas acepciones es una obra derivada y se publica también bajo CC BY-SA 4.0. Por eso se guardan como registros separados por licencia y no se mezclan con definiciones redactadas por el proyecto (MIT).
- El catálogo canónico reúne fichas con licencias distintas; cada ficha declara la suya y la entrada agrupada solo autoriza entrenamiento si todas sus partes lo permiten. Este lote no habilita entrenamiento: cambiarlo exige una decisión explícita y documentada sobre los modelos resultantes.

### Carochi (1645)

Facsímil: ejemplar de la Roman Catholic Archdiocese of Toronto digitalizado por University of Toronto en [Internet Archive](https://archive.org/details/artedelalenguam00caro) (México, Juan Ruyz, 1645; 286 imágenes). La obra es de dominio público; el mismo escaneo figura en Theological Commons (Princeton) como «No Known Copyright». Los folios se tomaron del índice y de los encabezados de capítulo del facsímil. Las notas de `corpus/grammar-notes-carochi-v1.json` (absolutivo, posesivos, prefijos de sujeto y objeto, plurales y locativos) están redactadas por el proyecto, citan libro, capítulo y folio, y esperan revisión especializada. No se redistribuye la transcripción OCR de Internet Archive ni la edición de Lockhart (2001, con derechos vigentes). `nahuatl_local.grammar_notes.for_unit()` las sirve a las unidades de lectura.

### Tlachia

Los folios nuevos siguen el flujo existente (`pictography_pipeline`): solo enlaces, campos del catálogo e imágenes cargadas desde su sitio, con atribución a las investigadoras e investigadores de cada documento. Ver [DICCIONARIO_PICTOGRAFICO.md](DICCIONARIO_PICTOGRAFICO.md).
