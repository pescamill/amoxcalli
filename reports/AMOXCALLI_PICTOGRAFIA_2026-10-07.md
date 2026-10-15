# Amoxcalli: palabras, lecturas y escritura pictográfica

Fecha: 7 de octubre de 2026.

## Análisis y decisión

La fortaleza del proyecto es aprender a comprender fragmentos con palabras básicas, ejercicios y fuentes consultables. El estudio de Tlachia mostró que una consulta documental necesita distinguir la denominación de un elemento, la aparición concreta de un glifo y los valores de sus componentes. Añadir más imágenes a las mismas fichas léxicas no resolvería esa diferencia.

Se conserva el recorrido educativo y se añade un índice independiente, enlazado desde el diccionario y desde Aprender. Su entrada guiada compara `calli` en tres fichas: Calpan registra `tecpan`; Telleriano registra `chiucnahui calli`; Huexotzinco registra `ichan tonalco *`, con `chan` como valor del componente. Estas son propuestas del catálogo consultado, atribuidas a su fuente. El ejercicio comprueba la distinción entre campos y no propone una interpretación nueva del manuscrito.

## Contenido publicado localmente

| Inventario | Cantidad |
|---|---:|
| Conjuntos documentales / láminas | 3 / 3 |
| Zonas | 21 |
| Glifos | 46 |
| Personajes | 14 |
| Registros de elementos por documento | 61 |
| Denominaciones exactamente distintas | 54 |
| Apariciones de componentes | 99 |

Fuentes del lote: [Calpan 073_08](https://tlachia.iib.unam.mx/calpan/073_08), [Telleriano 385_26r](https://tlachia.iib.unam.mx/telleriano/385_26r) y [Huexotzinco–Tianquiztenco 387_709v](https://tlachia.iib.unam.mx/mh-tianquiztenco/387_709v). El piloto no representa todo el contenido de esos documentos.

Glifos ofrece búsqueda y filtros, comparación de denominaciones entre documentos, fichas de apariciones con componentes y valores, navegación por documento/lámina/zona, vocabulario de los campos, descarga del índice público y una observación guiada. Conserva grafías, códigos, citas y marcas de incertidumbre. Las imágenes permanecen enlazadas al catálogo; los HTML consultados quedan en caché local ignorada por Git y su hash se conserva en el índice.

Permanecen las seis lecturas y sus 24 pasajes, las 575 acepciones y 578 formas del léxico, las palabras representativas de la primera página, los guardados y el repaso. El contenido de aprendizaje y sus hashes no cambian en esta integración. El laboratorio y sus pesos tampoco cambian.

## Ampliación reproducible

`nahuatl_local.pictography_pipeline` usa recetas con páginas explícitas, un parser sin LLM y un informe de excepciones. Limita cada lote a diez láminas y cien apariciones. Rechaza formatos desconocidos, IDs duplicados y contradicciones; difiere fichas sin lectura. La publicación es aditiva, conserva un respaldo y rechaza sustituciones de registros existentes. Repetir el piloto desde caché produjo candidato y publicación `unchanged`.

Los puentes con el léxico se declaran en la receta y solo se resuelven contra acepciones públicas. No se fusionan automáticamente variantes ortográficas. La importación no abre la base privada ni exporta perfiles o progreso. El índice declara `training: false`.

Arquitectura, límites, comandos y siguiente revisión: [Diccionario pictográfico](../docs/DICCIONARIO_PICTOGRAFICO.md).

## Cambio de nombre

Interfaz, manifiesto, descargas y documentación actual usan Amoxcalli. Se conservan las claves `scriptorium-study-v1`, la caché técnica y los identificadores de formatos históricos para mantener los datos existentes. Los nombres y textos originales de las fuentes permanecen intactos.

## Comprobaciones

- `.venv/bin/python -m unittest discover -s tests`: 188 pruebas, OK con un fallo esperado existente.
- Siete pruebas nuevas cubren separación de valores, privacidad, validación de fuentes, conservación de incertidumbre, excepciones e importación aditiva/idempotente.
- `npm run test:ui`: nueve grupos pasan; incluye búsqueda, filtros, fichas, observación guiada, enlaces didácticos, fallos de imagen y conservación del progreso previo.
- `npm run test:offline`: pasa la comprobación de caché y privacidad.
- Sintaxis de JavaScript y `git diff --check`: sin errores.
- Navegador real: presentación de escritorio y tres imágenes cargadas en la observación guiada. El ajuste de viewport no modificó el ancho efectivo; no se declara comprobación visual móvil del nuevo módulo.

La siguiente revisión de contenido debe cotejar el piloto con una persona especialista y comprobar con principiantes si la observación enseña la distinción entre denominación y lectura. La atribución documental y las pruebas técnicas no equivalen a una revisión lingüística concluida. No se declara colaboración ni aval institucional.
