# Un solo paradigma de datos · comparación antes/después (15 oct 2026)

Línea base: copia limpia de `86c217f`. Después: árbol de trabajo con `text.py`, `passages.py`, `lexicon.py` y `corpus/lexicon-catalog.json`.

| Evaluación | Antes | Después | Respuesta por respuesta |
|---|---|---|---|
| morphology_evaluation (top‑1 / dev / test / top‑3) | 77 % / 84 / 70 / 92 % | igual | Segmentación, cobertura, concordancia, IBM‑1 y Dice idénticos. La co‑ocurrencia (línea base) depende de `PYTHONHASHSEED` (empates sobre un `set`): con la misma semilla da lo mismo antes y después (0,248 / 0,238 / 0,228 con semillas 1/2/3). Cambia el orden de los ejemplos: los registros llegan ordenados por ID, como en el servidor. |
| evidence_evaluation (entrada top‑1 all) | 91,7 % | igual | Métricas idénticas. 4 respuestas muestran otra grafía de la misma acepción (`cuahuitl`→`quauitl`, `ehecatl`→`eecatl`, `ihuan`→`iuan`): ahora el orden es el del servidor. |
| documentary_retrieval_evaluation | 119/123 completas, 840/860 campos | igual | Métricas idénticas. El pasaje usa el modelo común (añade `line`, `period`, `variant_label`, `verification`; localizador unificado; `iso` vacío → `unknown` en 8 casos; la cita conserva el campo original vacío). Desaparece `version` de 352 registros (dato de la base, no del catálogo). |

Normalización: huellas de `phonemic_key`, `loose_key`, plegado, tokens y BM25 idénticas sobre 125 026 palabras y 83 728 textos; `explain` recorta ahora espacios en los extremos de las citas «…». Batería documental reconstruida: mismas 226 consultas y referencias; solo cambia el hash fijado de `documentary_evaluation.py`.

Migración de `data/community/voces.sqlite3`: respaldo `data/backups/voces-before-lexicon-catalog-v1.sqlite3`; 12 tablas preservadas, 1 317 registros, 0 ediciones locales, 0 propias, 0 ocultas.

Otros informes regenerados con `make reports`: el lote de glifos se reproduce con el mismo hash (`a8a377fa…`); `glyph-coverage-v7.json` pasa de 523 a 575 acepciones porque estaba desactualizado desde `a81c5bf` (HEAD `86c217f` ya daba 575), no por este cambio. Preparación de entrenamiento (`data/prepared/*.jsonl`) idéntica byte a byte.

Comprobación por grep: `!= 'Mn'` solo en `nahuatl_local/text.py`; `csv.reader(` y `'corpus/axolotl/axolotl.csv'` solo en `nahuatl_local/passages.py`; el único otro `def normalize` es `nah-ortho-1` (congelado). `tests/test_text.py` lo hace cumplir.
