# Evaluación del analizador morfológico

Analizador `nah-morph-1` · conjunto `morphology-gold-v1.json` · partición `all`. Generado por `python3 -m nahuatl_local.morphology_evaluation`.

## 1. Segmentación frente al conjunto de referencia

| Sistema | n | Segmentación exacta (top‑1) | top‑1 dev / test | En top‑3 | Raíz correcta (top‑1) |
|---|---:|---:|---:|---:|---:|
| unsegmented_baseline | 52 | 0% | 0% / 0% | 0% | 0% |
| rules_only | 52 | 15% | 8% / 22% | 62% | 15% |
| rules+dictionary | 52 | 65% | 68% / 63% | 81% | 60% |
| rules+corpus_em | 52 | 83% | 88% / 78% | 98% | 79% |
| full (rules+dictionary+corpus_em) | 52 | 85% | 88% / 82% | 96% | 77% |

Errores del sistema completo:

- `tlachihualli` → `tlachihual-li` (esperado `tla-chihua-l-li`, dev)
- `mochiuh` → `mochi-uh` (esperado `mo-chiuh`, dev)
- `nitlacua` → `ni-tlacua` (esperado `ni-tla-cua`, dev)
- `quitoque` → `quito-que` (esperado `qu-ito-que`, test)
- `Mexico` → `mexico` (esperado `Mexi-co`, test)
- `Tenochtitlan` → `tenochtitlan` (esperado `Tenoch-ti-tlan`, test)
- `tlaqualli` → `tlaqual-li` (esperado `tla-qua-l-li`, test)
- `tetlazohtlaliztli` → `tetlazohtlaliz-tli` (esperado `te-tlazohtla-liz-tli`, test)

## 2. Cobertura del diccionario en el corpus clásico

135,288 palabras (26,396 formas distintas) de los pasajes `nci` de Axolotl.

| Medida | Palabras | Formas distintas |
|---|---:|---:|
| Coincidencia exacta con una forma del diccionario | 28.0% | 3.9% |
| Raíz enlazada por el analizador (diccionario o partícula) | 60.2% | 26.6% |
| Con al menos un afijo o enlace explicado | 86.4% | — |

## 3. Concordancia por raíz

Para 1124 raíces del diccionario (≥4 fonemas) presentes en el corpus: la búsqueda por palabra exacta encuentra 10645 pasajes; el índice por raíz, 25350. 873 entradas ganan pasajes; 84 pierden alguno (1328 pasajes solo por búsqueda exacta).

Muestra para revisión humana de precisión: `reports/morphology-review/stem-hits-sample.csv`. Más pasajes no implica más aciertos: la muestra de revisión estima la precisión de los nuevos hallazgos.

| Entrada | Exacta | Por raíz |
|---|---:|---:|
| iipan | 0 | 1036 |
| Xiuitl | 176 | 1075 |
| ihuan, iuan | 172 | 972 |
| toca, tocatl | 11 | 683 |
| ihcuac | 105 | 597 |
| tlahtoa | 2 | 435 |
| ihtoa | 1 | 413 |
| mexihcatl | 0 | 312 |

## 4. Pistas de glosa del corpus paralelo frente a Molina

101 entradas con raíz presente en ≥2 pasajes. Acierto si una palabra propuesta (normalizada) aparece en la definición de Molina de esa entrada. Molina es independiente del corpus paralelo; la coincidencia ortográfica del s. XVI es aproximada.

| Método | Precisión@1 | Acierto en top‑3 |
|---|---:|---:|
| cooccurrence | 19% | 36% |
| dice | 23% | 36% |
| ibm1 | 30% | 39% |

Ejemplos (IBM‑1):

- `eecatl` — Molina: «viento» → viento
- `cuahuitl` — Molina: «madera» → arbol, piedra, madera
- `metztli` — Molina: «mes» → mes, dia, luna
- `Cacahuaxochitl` — Molina: «flor llamada cacahuaxochitl» → flor, cacao
- `calli` — Molina: «casa» → casa
- `citlalin` — Molina: «estrella» → estrella, humeo
- `coatl` — Molina: «serpiente» → serpiente, comprar, barrio
- `Cuicatl` — Molina: «canto / canción» → canto, cantor
- `Ecapitzactli` — Molina: «ayre sotil y delgado.» → —
- `Ecaticpac` — Molina: «encima del ayre.» → air, pec

## Límites

- El conjunto de referencia es pequeño y lo redactó el equipo a partir de paradigmas de gramáticas; requiere revisión especializada.
- La partición `dev` se usó para ajustar costes. Tras la primera medición de `test` se corrigieron dos fallos generales (concordancia de categoría entre análisis y entrada; sustantivos breves registrados completos, como *atl*); la primera medición se conserva en `reports/morphology-evaluation-first-test-run.json`. Con 27 casos, un caso equivale a ~4 puntos.
- Molina (1571) no es un diccionario completo ni moderno: una pista correcta puede no aparecer en su definición.
- Ninguna cifra mide comprensión lectora ni calidad de traducción.

Tiempo de ejecución: 18.7 s.
