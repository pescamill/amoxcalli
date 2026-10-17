# Fichas y originales en Preguntar · `cards-v1`

Desde el 16 de octubre de 2026 la antigua vista **Consultar fichas** (`#consultar`) vive dentro de **Preguntar**. Debajo de la respuesta de una palabra, la sección **Fichas y originales** muestra los registros con sus campos literales: escritura original frente a normalización catalogada (y si coinciden), acepción vinculada, pasaje del archivo (original náhuatl, español conservado, obra, variedad) o elemento y aparición de Tlachia, cada campo con su fila, su archivo de origen (SHA256) y su URL. Preguntar acepta también el ID de una ficha (`axolotl-14546`, `lex-gdn-m2-147139`, el código de una aparición) o una pregunta documental que lo contenga. Comparar grafías significa mostrar ambos campos y su igualdad literal; no elegir un significado ni interpretar un glifo. Se consulta texto del catálogo; no se procesan ni copian imágenes. Los enlaces anteriores a `#consultar/…` abren `#preguntar/…` con la misma consulta y el mismo retorno al pasaje de lectura.

## Cómo se eligen las fichas

`nahuatl_local.cards` (solo stdlib) construye una ficha por registro público actual de `CorpusStore`, por cada uno de los 16.111 pasajes del archivo y por cada fila de las tablas del catálogo pictográfico. **No tiene ranking propio**: la API `GET /api/ask/cards?q=…` devuelve, en este orden,

1. los IDs literales que contiene la consulta (un ID retirado no se lee como palabras);
2. si la consulta es una palabra, las fichas del grupo de término que resuelve la búsqueda única (`terms.resolve`: formas con su acepción, acepciones sin forma, glifos del diccionario, elementos y apariciones de Tlachia) y sus cinco primeros pasajes;
3. si es una pregunta más larga, las fichas de cada palabra del diccionario mencionada (grafía exacta por clave laxa, hasta 8 grupos). No cuentan las palabras funcionales del español que también son grafías del diccionario (*a*, *y*, *o*, *e*, *de*…) salvo escritas como alternativa explícita con barra (*o / o*, *titi / y*), ni palabras con acento español que la entrada no escribe así (*náhuatl*, *México*).

Hasta 40 fichas, con aviso si hay más; sin coincidencias, «No hay fichas registradas para esta consulta; no demuestra ausencia en la lengua». La API vuelve a comprobar las fichas públicas en cada petición: si cambia una publicación, se retira un registro o cambia un archivo fuente, reconstruye las fichas y no conserva una versión retirada.

Antes (`documentary-lookup-v1`, módulo `documentary_retrieval`, retirado) un índice invertido propio puntuaba identificadores (1.000 puntos), etiquetas completas por tokens (100 más longitud) y solapamiento de tokens ponderado por frecuencia inversa, con una lista de palabras funcionales. Duplicaba la búsqueda de términos y se medía aparte; ahora las palabras pasan por el índice de términos, como en Diccionario, Archivo y la respuesta de Preguntar.

Las formas recuperadas llevan su acepción vinculada; las acepciones distintas permanecen separadas. La consulta muestra un aviso cuando hay más de 20 coincidencias y cuando no encuentra evidencia. Una coincidencia relacionada no acredita una respuesta completa. IDs explícitos y preguntas sobre campos son una prueba de consulta documental, no de comprensión general del lenguaje.

## Medición y reproducción

```sh
make eval     # python -m nahuatl_local.evaluate_all: incluye las 123 consultas documentales
make check    # vuelve a medir y falla si alguna cifra cambió
python -m nahuatl_local.evaluate_all --only documentary   # solo esta parte; imprime, no escribe
```

El arnés único (`evaluate_all.documentary`) lee la batería `configs/documentary-evaluation-v1.json`, comprueba que se reconstruye desde los datos y mide cada una de las 123 consultas textuales de desarrollo; las fichas solo reciben la pregunta. La reserva se conserva intacta y no se usa. Una consulta es **completa** si las fichas contienen todos los campos de referencia con valor, hash de fila y hash de archivo idénticos, más sus fuentes y URLs, y todas las citas devueltas son válidas (`PublicSources.citation_valid`: valor, fila, archivo y URL documentada). Compartir Molina/GDN no basta. Cobertura, abstención y campos exactos se informan por separado, por tarea (glosa léxica y comparación), en [reports/EVALUACION.md](../reports/EVALUACION.md#fichas-documentales-preguntar).

**Antes y después de integrar Consultar en Preguntar (16 oct 2026):** con el ranker anterior, 119/123 completas, 121 con fichas, 121/121 con citas válidas, 770/790 campos exactos; con las fichas de Preguntar, 121/123, 121, 121/121 y 780/790. Ninguna consulta empeoró (se compararon las 123 una por una). Las dos que ahora se completan son *Titi / Y* (glosa y comparación): la barra marca *y* como grafía pedida; siguen en abstención *A* (glosa y comparación), cuya grafía es una palabra funcional del español.

Tiempos (construcción y media por consulta) se guardan en `reports/evaluation.json`, fuera de la compuerta.

Los campos editados públicamente en esta instalación se identifican como `public_records`, distintos de la transcripción distribuida; no se certifican como evidencia literal de una fila congelada. Las fuentes mantienen condiciones originales. La consulta local no habilita entrenamiento, evaluación con imágenes, copia de imágenes ni envío externo. Cotejo primario, juicio lingüístico y ensayo con personas siguen pendientes.

## Registro de desarrollo del ciclo 006

Primera corrida: 119/123 casos completos, 121 con coincidencias, 2 abstenciones; 840/860 campos requeridos. Se conservan las exclusiones de A y Y dentro de preguntas extensas. Una comprobación independiente con «agua» mostró que las formas no heredaban las etiquetas españolas explícitas de su acepción vinculada. Se añadieron esas etiquetas y aliases al índice de su forma para permitir la consulta bilingüe con original y fuente juntos; no se infieren sinónimos. Esta modificación se registra antes de la corrida final y no responde a claves de reserva. También se separó validez de citas devueltas de cobertura de todas las URLs solicitadas: una respuesta parcial puede tener citas válidas y seguir incompleta. La corrida inicial se conserva en el respaldo del informe.

La verificación final en navegador detectó que la política CSP bloqueaba el estilo inline de los originales en PRE, causando desbordamiento horizontal. La regla `.card.documentary-hit pre` vive ahora en `/amoxcalli.css`, con `white-space:pre-wrap` y corte de cadenas largas; la presentación no requiere excepciones CSP. El stylesheet entra en hashes del informe y del diagnóstico. La prueba DOM comprueba estilo calculado y ausencia de inline, y el coordinador verifica anchura real en navegador.

## Dependencias separadas · ciclo 014 (histórico)

Hasta el 16 de octubre de 2026, `documentary_retrieval_evaluation.IMPLEMENTATION` y `documentary_evaluation.FIXED` fijaban por hash las entradas de la medición (ranking, store, corpus, fuentes, batería, receta y evaluador) y `documentary_laboratory` derivaba de ella la comparación del Laboratorio. Ahora la compuerta vuelve a medir y compara cifras: solo la disparan cambios que mueven una respuesta, no la interfaz ni la documentación. `documentary_evaluation.FIXED` conserva únicamente archivos de datos; el código de la receta queda cubierto por la reconstrucción completa de la batería.

UI, navegación, CSS, API de presentación y guías de proceso nunca fueron entradas de la medición; tampoco lo son ahora.
