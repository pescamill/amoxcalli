# Evaluación del analizador morfológico

Analizador `nah-morph-1` · conjunto `morphology-gold-v1.json` · partición `all`. Generado por `python3 -m nahuatl_local.morphology_evaluation`.

## 1. Segmentación frente al conjunto de referencia

| Sistema | n | Segmentación exacta (top‑1) | top‑1 dev / test | En top‑3 | Raíz correcta (top‑1) |
|---|---:|---:|---:|---:|---:|
| unsegmented_baseline | 52 | 0% | 0% / 0% | 0% | 0% |
| rules_only | 52 | 15% | 8% / 22% | 62% | 15% |
| rules+dictionary | 52 | 44% | 48% / 41% | 75% | 40% |
| rules+corpus_em | 52 | 73% | 80% / 67% | 92% | 69% |
| full (rules+dictionary+corpus_em) | 52 | 77% | 84% / 70% | 92% | 71% |

Errores del sistema completo:

- `tlachihualli` → `tlachihual-li` (esperado `tla-chihua-l-li`, dev)
- `itoca` → `ito-ca` (esperado `i-toca`, dev)
- `nitlacua` → `ni-tlacua` (esperado `ni-tla-cua`, dev)
- `niquitohua` → `ni-qui-tohua` (esperado `ni-qu-itohua`, dev)
- `ticochi` → `ti-c-ochi` (esperado `ti-cochi`, test)
- `nicochiz` → `ni-c-ochi-z` (esperado `ni-cochi-z`, test)
- `quitoa` → `qui-toa` (esperado `qu-itoa`, test)
- `quitoque` → `quito-que` (esperado `qu-ito-que`, test)
- `ytoca` → `yto-ca` (esperado `y-toca`, test)
- `Tenochtitlan` → `tenoch-titlan` (esperado `Tenoch-ti-tlan`, test)
- `tlaqualli` → `tla-qual-li` (esperado `tla-qua-l-li`, test)
- `tetlazohtlaliztli` → `tetlazohtlaliz-tli` (esperado `te-tlazohtla-liz-tli`, test)

## 2. Cobertura del diccionario en el corpus clásico

135,288 palabras (26,396 formas distintas) de los pasajes `nci` de Axolotl.

| Medida | Palabras | Formas distintas |
|---|---:|---:|
| Coincidencia exacta con una forma del diccionario | 20.3% | 0.8% |
| Raíz enlazada por el analizador (diccionario o partícula) | 41.8% | 3.9% |
| Con al menos un afijo o enlace explicado | 84.1% | — |

## 3. Concordancia por raíz

Para 117 raíces del diccionario (≥4 fonemas) presentes en el corpus: la búsqueda por palabra exacta encuentra 3493 pasajes; el índice por raíz, 6391. 95 entradas ganan pasajes; 3 pierden alguno (4 pasajes solo por búsqueda exacta).

Muestra para revisión humana de precisión: `reports/morphology-review/stem-hits-sample.csv`. Más pasajes no implica más aciertos: la muestra de revisión estima la precisión de los nuevos hallazgos.

| Entrada | Exacta | Por raíz |
|---|---:|---:|
| Xiuitl | 176 | 1075 |
| ihuan, iuan | 172 | 972 |
| itta | 6 | 133 |
| Yehua, Yeua | 31 | 125 |
| Onca | 70 | 155 |
| Maceualli | 14 | 96 |
| tepetl | 44 | 124 |
| Oncan | 838 | 904 |

## 4. Pistas de glosa del corpus paralelo frente a Molina

101 entradas con raíz presente en ≥2 pasajes. Acierto si una palabra propuesta (normalizada) aparece en la definición de Molina de esa entrada. Molina es independiente del corpus paralelo; la coincidencia ortográfica del s. XVI es aproximada.

| Método | Precisión@1 | Acierto en top‑3 |
|---|---:|---:|
| cooccurrence | 24% | 35% |
| dice | 23% | 36% |
| ibm1 | 30% | 39% |

Ejemplos (IBM‑1):

- `xochitl` — Molina: «flor» → flor
- `cuahuitl` — Molina: «árbol» → arbol, piedra, madera
- `xochicuahuitl` — Molina: «árbol florido» → arbol, pajaro, anda
- `calli` — Molina: «casa» → casa
- `tonatiuh` — Molina: «sol» → sol, hacia
- `metztli` — Molina: «luna» → mes, dia, luna
- `itta` — Molina: «ver» → vio, ver, vieron
- `tochtli` — Molina: «conejo» → ano, conejo
- `mazatl` — Molina: «venado» → venado, conejo
- `tototl` — Molina: «ave» → ave, nuestra, pajaro

## Límites

- El conjunto de referencia es pequeño y lo redactó el equipo a partir de paradigmas de gramáticas; requiere revisión especializada.
- La partición `dev` se usó para ajustar costes. Tras la primera medición de `test` se corrigieron dos fallos generales (concordancia de categoría entre análisis y entrada; sustantivos breves registrados completos, como *atl*); la primera medición se conserva en `reports/morphology-evaluation-first-test-run.json`. Con 27 casos, un caso equivale a ~4 puntos.
- Molina (1571) no es un diccionario completo ni moderno: una pista correcta puede no aparecer en su definición.
- Ninguna cifra mide comprensión lectora ni calidad de traducción.

Tiempo de ejecución: 52.9 s.
