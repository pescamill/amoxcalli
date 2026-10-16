# reports/

Solo informes vigentes. Los informes de ciclo (registros de pruebas, entregas fechadas, diagnósticos, paquetes de revisión) se retiraron el 15 de octubre de 2026; su resumen está en [docs/HISTORIA.md](../docs/HISTORIA.md) y su contenido sigue en el historial de git.

Un cambio solo de interfaz (`platform.py`, `platform_web/*`, pruebas DOM) **no** exige regenerar nada aquí: la presentación se verifica con `make test-ui`. Las compuertas de hash cubren solo entradas medidas: ranking, datos, batería y evaluador (`documentary_retrieval_evaluation.IMPLEMENTATION` y `documentary_evaluation.FIXED`).

## Regenerables sin modelo ni red · `make reports` (comprobar con `make check`)

| Archivo | Comando | Lo muestra |
|---|---|---|
| `documentary-evaluation-validation-v1.json` | `python3 -m nahuatl_local.documentary_evaluation` | Validación de la batería `configs/documentary-evaluation-v1.json` |
| `documentary-retrieval-v1.json` | `python3 -m nahuatl_local.documentary_retrieval_evaluation` | Consulta documental: 119/123 completas, 840/860 campos |
| `documentary-laboratory-v1.json` | `python3 -m nahuatl_local.documentary_laboratory` | Laboratorio · Modelo y progreso (deriva del anterior) |
| `evidence-evaluation.json`, `EVIDENCIA_EVALUACION.md` | `python3 -m nahuatl_local.evidence_evaluation` | Preguntar ([docs/EVIDENCIA.md](../docs/EVIDENCIA.md)) |
| `morphology-evaluation.json`, `MORFOLOGIA_EVALUACION.md`, `morphology-review/stem-hits-sample.csv` | `python3 -m nahuatl_local.morphology_evaluation` | Analizar cualquier palabra ([docs/MORFOLOGIA.md](../docs/MORFOLOGIA.md)) |
| `term-groups-evaluation.json`, `TERMINOS_EVALUACION.md` | `python3 -m nahuatl_local.term_evaluation` | Grupos de término: grafías, glifos y precisión ([evaluation/term-groups-v1.json](../evaluation/term-groups-v1.json)) |
| `glyph-coverage-v7.json` | `python3 -m nahuatl_local.glyph_linker` (en `make reports`, sin reescribir el lote del corpus) | Cobertura de referencias glíficas |

Las cifras de tiempo y memoria cambian en cada corrida; las métricas no deben cambiar si no cambian las entradas medidas.

## Líneas base de la primera corrida sobre prueba (no se regeneran)

`morphology-evaluation-first-test-run.json`, `evidence-evaluation-first-test-run.md` y `term-groups-evaluation-first-test-run.json` conservan el primer resultado sobre la partición `test`, antes de corregir fallos. Los informes vigentes las citan para que la mejora posterior no se confunda con ajuste a la prueba.

## Laboratorio LLM · requieren `requirements.txt`, `data/prepared/` y pesos · `make reports-model`

| Archivo | Comando |
|---|---|
| `benchmark-retrieval-validation-current*.json`, `.review.csv` | `python3 -m nahuatl_local.benchmark --retrieval-only --split validation --output reports/benchmark-retrieval-validation-current-full.json` |
| `benchmark-{base,adapter,adapter-rag,continued-unseen,automatic-best}.json` | `python3 -m nahuatl_local.benchmark [--adapter …] [--rag] --output …` (ver [MODEL_CARD.md](../MODEL_CARD.md)) |
| `webapp-model-smoke.json` | `python3 scripts/check-local-model.py` |

## Procedencia citada por datos distribuidos (inmutable)

No se regeneran ni se borran mientras los datos que los citan existan:

- `editorial-pipeline/batch-007/` — citado por `corpus/editorial-batch-007-v9.json` (lote publicado); también es el fixture de `tests/test_editorial_*`.
- `editorial-pipeline/batch-008-v10/`, `batch-009-v11/` — citados por las propuestas no publicadas `editorial/batch-00{8,9}-*.json`.
- `FLOR_CICLO_2026-09-30.md`, `platform-ui-flor-2026-09-30.txt` — evidencia citada por `editorial/lesson-decisions.json`.
- `corpus-preparation-legacy.json`, `download-all.json` — datos y hashes de descarga de los adaptadores en `outputs/`, citados por `MODEL_CARD.md`.
