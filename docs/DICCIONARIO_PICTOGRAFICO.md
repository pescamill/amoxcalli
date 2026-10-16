# Diccionario pictográfico de Amoxcalli

## Decisión y propósito

Amoxcalli comienza por aprender a comprender fragmentos de náhuatl clásico. El diccionario de palabras, las doce lecturas, sus ejercicios y el cuaderno personal siguen siendo la entrada principal. El espacio **Glifos** permite seguir una pregunta hasta una aparición gráfica y su análisis documental.

Una palabra, una denominación de elemento y la lectura de un glifo no son entidades intercambiables. Por ejemplo, las fichas de Tlachia seleccionadas denominan un elemento `calli`, pero registran `tecpan`, `calli` o `chan` como valores en apariciones diferentes. El recorrido «Aprender a observar» enseña a distinguir esos campos comparando tres fichas; su pregunta se refiere al dato del catálogo, no pretende validar una lectura inédita.

Se adopta una estructura documental inspirada en [Tlachia](https://cen.sup-infor.com/home/tlachia), con atribución y enlaces. Su [introducción](https://tlachia.iib.unam.mx/documentos/introduccion), [terminología](https://tlachia.iib.unam.mx/documentos/terminologia) y [método](https://tlachia.iib.unam.mx/documentos/finalidad-de-tlachia) permiten consultar el marco original. No se declara una colaboración institucional ni se atribuye el análisis de sus fichas a Amoxcalli.

## Entidades y límites

| Entidad | Identidad y contenido |
|---|---|
| Documento | Título, atribución, enlace y alcance del subconjunto incorporado |
| Lámina | Documento, localizador del catálogo, imagen enlazada y SHA-256 del HTML consultado |
| Zona | Lámina y código originales; división del análisis, no una división histórica asumida |
| Aparición | Código original de glifo/personaje, lectura literal, imagen, citas y zona cuando existe |
| Elemento | Registro por documento: designación literal, sentido, clave temática e imagen del catálogo |
| Componente | Enlace de una aparición con un elemento y los valores registrados en ese contexto |
| Puente léxico | Relación explícita de **denominación** con una acepción didáctica pública y una nota de alcance |

Los elementos se identifican por documento y clave; no se fusionan porque compartan nombre o imagen. El índice agrupa denominaciones exactamente iguales para facilitar la consulta, conservando sus registros independientes. `cohuatl` y `coatl`, por ejemplo, no se equiparan automáticamente. La agrupación no acredita identidad paleográfica.

Los sentidos, segmentaciones, valores y citas reproducen campos del catálogo, conservando interrogaciones, asteriscos y grafías. Los párrafos lexicográficos GDN incrustados se excluyen del parser: no se confunde un contexto de diccionario con una cita del glifo. Las fichas sin componentes o sin valores declaran esa ausencia. No hay segmentación automática ni interpretación de píxeles.

Las claves temáticas organizan la consulta; no se presentan como una taxonomía tradicional nahua. La estructura de deidades del Telleriano sigue el catálogo consultado y su [estudio](https://tlachia.iib.unam.mx/telleriano/estudio).

## Primer lote

`tlachia-pilot-v1` contiene **3 conjuntos, 3 láminas, 21 zonas, 46 glifos, 14 personajes, 61 registros de elementos por documento, 54 denominaciones distintas y 99 apariciones de componentes**. No son 60 palabras nuevas ni el catálogo completo de esos documentos.

- [Calpan, 073_08](https://tlachia.iib.unam.mx/calpan/073_08).
- [Telleriano-Remensis, 385_26r](https://tlachia.iib.unam.mx/telleriano/385_26r).
- [Matrícula de Huexotzinco, Tianquiztenco, 387_709v](https://tlachia.iib.unam.mx/mh-tianquiztenco/387_709v).

La fecha de consulta del lote es el 7 de octubre de 2026. Las comprobaciones son de catálogo, no cotejo del manuscrito ni revisión lingüística especializada. Las páginas HTML completas quedan en caché local ignorada por Git; el índice distribuido conserva su hash y los campos seleccionados.

El léxico mantiene **575 acepciones y 578 formas**, sus imágenes y las 24 palabras representativas de la primera página. Sus referencias contextuales anteriores no se convierten en componentes documentales del índice nuevo.

## Ampliar por lotes

### Segunda lámina de Telleriano · 7 de octubre de 2026

El lote `tlachia-telleriano-385-26v-v2` añade [Telleriano-Remensis, 385_26v](https://tlachia.iib.unam.mx/telleriano/385_26v): 31 apariciones y 68 componentes. Reutiliza 18 elementos del mismo documento y añade 26, conservando íntegramente las fichas anteriores. El índice actual reúne **3 conjuntos, 4 láminas, 32 zonas, 77 glifos, 14 personajes, 87 registros de elementos, 77 denominaciones distintas y 167 componentes**, con 9 puentes léxicos explícitos.

Cuando otra lámina documenta un elemento existente, la publicación permite una URL de página distinta únicamente si todos los demás campos coinciden. Conserva la URL y las notas originales del elemento; la aparición nueva mantiene su propio localizador. Un cambio de sentido, designación, imagen o notas sigue siendo un conflicto.

### Nueve láminas más de Telleriano · 8 de octubre de 2026

Los lotes v3–v6 añaden 220 apariciones de las láminas 385_21v, 385_22r, 385_22v, 385_23r, 385_23v, 385_24r, 385_24v, 385_25r y 385_25v. El índice reúne ahora **3 conjuntos, 13 láminas, 155 zonas, 297 glifos, 14 personajes, 152 registros de elementos, 142 denominaciones distintas y 613 componentes**. Conserva los 9 puentes léxicos y todas las filas anteriores, incluidas sus notas y URLs.

Se reutilizó HTML de fuente cacheado, en lotes de 86, 25, 86 y 23 apariciones, sin llamadas al LLM para extraer ni enlazar datos. Cada publicación tiene receta, candidato, informe y respaldo; repetirla conserva los bytes. La comprobación del catálogo y su procedencia no constituye un cotejo primario del manuscrito. Hay 79 apariciones sin cita y 70 sin componentes; esas ausencias permanecen explícitas.

La meta cuantitativa de 300 apariciones está cubierta. El siguiente paso técnico es preparar consultas documentales de desarrollo y una reserva independiente para evaluar recuperación y futuras comparaciones del Laboratorio. La revisión especializada y la prueba del recorrido con personas siguen pendientes.

### Ocho láminas más de Telleriano, enlazadas al índice de términos · 16 de octubre de 2026

Los lotes `tlachia-telleriano-385-01v-19v-v7` (385_01v, 385_02v, 385_04r, 385_08r, 385_19v; 90 apariciones) y `tlachia-telleriano-385-03v-15r-v8` (385_03v, 385_11r, 385_15r; 79 apariciones) se eligieron entre las láminas de Telleriano no incorporadas por el número de elementos **nuevos** cuya denominación el índice de términos resuelve a una entrada del diccionario (`terms.TermIndex.resolve`): *apantli, olli, tototl, tzontecomatl, yauhtli, metztli, tepetl, tetl, ilhuitl, tilmatli, topilli, chimalli, atlatl, centli, petlatl*… El índice reúne ahora **3 conjuntos, 21 láminas, 221 zonas, 197 registros de elementos, 185 denominaciones distintas y 480 apariciones**; 138 denominaciones se resuelven a una entrada del diccionario (109 con el catálogo anterior a estas láminas). Las 311 apariciones y los 152 elementos anteriores se conservan byte a byte (respaldos `catalog-before-…-v7/v8.json`).

Mismo flujo y límites: páginas consultadas una vez y guardadas en la caché local, imágenes solo enlazadas a Tlachia, atribución a Bertina Olmedo (INAH) y a Tlachia, sin LLM, sin cotejo del manuscrito ni revisión lingüística. Se reutilizan los nueve puentes léxicos explícitos; no se añadieron puentes nuevos. El permiso para incorporar más fichas está solicitado en un borrador sin enviar ([permisos/unam-gdn-tlachia.md](permisos/unam-gdn-tlachia.md)).

### Comandos

Crear una receta con ID nuevo siguiendo `editorial/pictography-tlachia-v1.json`. Definir documentos, URLs de láminas explícitas y puentes léxicos justificados. Un lote admite hasta diez láminas y cien apariciones. No hay rastreo recursivo ni llamadas al LLM.

Preparar una propuesta usando la caché; `--fetch` consulta solo páginas ausentes, mediante HTTPS con certificados verificados:

```bash
.venv/bin/python -m nahuatl_local.pictography_pipeline \
  --recipe editorial/pictography-mi-lote-v2.json \
  --output editorial/pictography-mi-lote-v2-candidate.json --fetch
```

Revisar el candidato y su informe: códigos, lecturas, componentes, atribuciones, excepciones y puentes. La ausencia de lectura se difiere; un formato irreconocible, IDs duplicados o denominaciones contradictorias detienen el ensamblado.

Incorporar un lote revisado de forma aditiva:

```bash
.venv/bin/python -m nahuatl_local.pictography_pipeline \
  --recipe editorial/pictography-mi-lote-v2.json \
  --output editorial/pictography-mi-lote-v2-candidate.json \
  --publish corpus/pictography/catalog.json
```

Repetir los mismos datos devuelve `unchanged`. Una sustitución de ID se rechaza; los cambios de interpretación necesitan una revisión explícita y versionada, no otra importación automática. Antes de añadir fichas se conserva un respaldo del índice público. La base de Voces, las propuestas privadas y el progreso del navegador no se abren ni se modifican.

El índice se consulta mediante `GET /api/pictography`. La plataforma resuelve los puentes solo contra acepciones actualmente públicas. Un fallo de esta consulta no bloquea las lecturas.

## Permisos y siguientes pasos

Las imágenes permanecen enlazadas a Tlachia, con atribución y acceso al contexto. No se descargan para redistribuirlas ni se relicencian como MIT. El índice declara `training: false`; incorporarlo no alimenta el LLM.

Las ampliaciones son transcripciones estructuradas de catálogo con comprobaciones técnicas. Sigue pendiente revisar el lote piloto con una persona especialista y probar si el recorrido permite distinguir denominación y lectura. Las nuevas relaciones léxicas o interpretaciones requieren evidencia y revisión explícitas. Una posible integración futura con un editor de aportaciones requiere mantener este nivel de evidencia y la revisión de permisos; la interfaz actual no publica modificaciones pictográficas.

## Nombre y compatibilidad

El nombre visible, manifiesto, descargas y documentación actual usan **Amoxcalli**. Se conservan `scriptorium-study-v1`, la caché técnica y los identificadores históricos de formatos/archivos para preservar datos existentes y consumidores. Renombrar esas claves no mejora el aprendizaje y podría perder progreso. El cambio de marca no modifica textos de las fuentes ni los hashes de las lecturas.
