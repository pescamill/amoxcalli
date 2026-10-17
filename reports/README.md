# reports/

Solo informes vigentes. Los informes de ciclo (registros de pruebas, entregas fechadas, diagnósticos, paquetes de revisión) se retiraron el 15 de octubre de 2026; su resumen está en [docs/HISTORIA.md](../docs/HISTORIA.md) y su contenido sigue en el historial de git.

Un cambio solo de interfaz (`platform.py`, `platform_web/*`, pruebas DOM) o de documentación **no** mueve ninguna cifra: la presentación se verifica con `make test-ui`. La compuerta (`make check`) vuelve a medir y compara solo cifras, de modo que solo la disparan las entradas medidas: datos, conjuntos de evaluación, analizador, índice de términos, Preguntar y sus fichas. Tiempos y memoria se guardan aparte y no cuentan.

## Una sola evaluación · `make eval` (comprobar con `make check`)

| Archivo | Comando | Lo muestra |
|---|---|---|
| `EVALUACION.md`, `evaluation.json` | `make eval` = `python3 -m nahuatl_local.evaluate_all` | Una tabla con morfología, índice de términos, Preguntar y fichas documentales, por partición (dev / test), y el detalle de cada componente: fallos, líneas base y límites |
| `morphology-review/stem-hits-sample.csv` | (lo escribe `make eval`) | Muestra de 60 hallazgos de la concordancia por raíz para revisión humana |

Conjuntos medidos: `evaluation/morphology-gold-v1.json`, `evaluation/term-groups-v1.json`, `evaluation/evidence-questions-v1.json` y la batería documental `configs/documentary-evaluation-v1.json` (123 consultas textuales de desarrollo; su reserva no se usa). La batería se reconstruye desde los datos con `python3 -m nahuatl_local.documentary_evaluation` cuando cambian; el arnés rechaza una batería obsoleta. Para ajustar sin escribir: `python3 -m nahuatl_local.evaluate_all --only terms --split dev` (o `morphology`, `evidence`, `documentary`).

Hasta el 16 de octubre de 2026 había cuatro evaluaciones con informe y compuerta propios (`documentary_evaluation` + `documentary_retrieval_evaluation` + `documentary_laboratory`, `evidence_evaluation`, `term_evaluation`, `morphology_evaluation`: `EVIDENCIA_EVALUACION.md`, `MORFOLOGIA_EVALUACION.md`, `TERMINOS_EVALUACION.md`, `documentary-retrieval-v1.json`, `documentary-laboratory-v1.json`…). Sus métodos de medida siguen en esos módulos; el arnés los reúne y escribe un solo informe. Los anteriores están en el historial de git.

## Cobertura · `make reports` (= `make eval` + estos)

| Archivo | Comando | Lo muestra |
|---|---|---|
| `UNIDADES_COBERTURA.md`, `units-coverage.json`, `units-review-queue.json` | `python3 -m nahuatl_local.units` | Unidades de gramática: respaldo automático de cada respuesta y cola editorial |
| `glyph-coverage-v7.json` | `python3 -m nahuatl_local.glyph_linker` (en `make reports`, sin reescribir el lote del corpus) | Cobertura de referencias glíficas |

## Líneas base de la primera corrida sobre prueba (no se regeneran)

`morphology-evaluation-first-test-run.json`, `evidence-evaluation-first-test-run.md` y `term-groups-evaluation-first-test-run.json` conservan el primer resultado sobre la partición `test`, antes de corregir fallos. Los informes vigentes las citan para que la mejora posterior no se confunda con ajuste a la prueba.

## Laboratorio LLM (histórico)

Los informes del modelo Qwen3-0.6B + LoRA (`benchmark-*.json`, `webapp-model-smoke.json`, `corpus-preparation-legacy.json`, `download-all.json`, `documentary-laboratory-v1.json`) se movieron con su código a [experiments/llm/reports/](../experiments/llm/reports/). Ver [experiments/llm/README.md](../experiments/llm/README.md).

## Procedencia citada por datos distribuidos (inmutable)

No se regeneran ni se borran mientras los datos que los citan existan:

- `wiktionary-import-v12.json` — selección, duplicados omitidos y comprobación de preservación del lote `corpus/wiktionary-lexicon-v12.json` (`python -m nahuatl_local.wiktionary_import --check` lo verifica contra la caché).
- `editorial-pipeline/batch-007/` — citado por `corpus/editorial-batch-007-v9.json` (lote publicado); también es el fixture de `tests/test_editorial_*`.
- `editorial-pipeline/batch-008-v10/`, `batch-009-v11/` — citados por las propuestas no publicadas `editorial/batch-00{8,9}-*.json`.
- `FLOR_CICLO_2026-09-30.md`, `platform-ui-flor-2026-09-30.txt` — evidencia citada por `editorial/lesson-decisions.json`.
- `experiments/llm/reports/corpus-preparation-legacy.json`, `download-all.json` — datos y hashes de descarga de los adaptadores en `outputs/`, citados por `experiments/llm/MODEL_CARD.md`.
