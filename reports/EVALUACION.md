# Evaluación de Amoxcalli

Una sola tabla, regenerable con `make eval` (`python -m nahuatl_local.evaluate_all`); `make check` vuelve a medir y falla si alguna cifra cambió sin regenerar este informe. Sin modelos ni red. Los conjuntos son pequeños y los escribió el equipo técnico: miden comportamiento técnico, no sustituyen la revisión de una persona experta.

`dev` se usa para ajustar; `test` solo para medir (la primera medición de cada conjunto de prueba, antes de corregir fallos, se conserva en `reports/*-first-test-run.*`). La batería documental se mide en desarrollo; su reserva no se usa.

| Componente | Conjunto | Medida | dev | test | total |
|---|---|---|---:|---:|---:|
| Morfología | `evaluation/morphology-gold-v1.json` | Segmentación exacta (top‑1) | 88 % | 82 % | 85 % |
| Morfología | `evaluation/morphology-gold-v1.json` | Segmentación en top‑3 | 100 % | 93 % | 96 % |
| Morfología | `evaluation/morphology-gold-v1.json` | Raíz correcta (top‑1) |  |  | 77 % |
| Morfología | Pasajes `nci` de Axolotl | Palabras con raíz enlazada |  |  | 60.2 % |
| Morfología | Molina (entradas evaluables) | Pistas de glosa, precisión@1 (IBM‑1) |  |  | 30 % |
| Índice de términos | `evaluation/term-groups-v1.json` | Consulta → grupo (top‑1) | 96.7 % | 85.7 % | 90.3 % |
| Índice de términos | `evaluation/term-groups-v1.json` | Grafías seguras | 96.4 % | 86.4 % | 92 % |
| Índice de términos | `evaluation/term-groups-v1.json` | Glifos | 100 % | 100 % | 100 % |
| Índice de términos | `evaluation/term-groups-v1.json` | Precisión de grafías (etiquetadas) | 100 % | 100 % | 100 % |
| Índice de términos | `evaluation/term-groups-v1.json` | Precisión de glifos (etiquetados) | 100 % | 100 % | 100 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Entrada top‑1 | 90 % | 92.3 % | 91.7 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Entrada top‑3 | 90 % | 92.3 % | 91.7 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Con pasaje pertinente | 100 % | 100 % | 100 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Precisión de pasajes | 99.2 % | 96.4 % | 97.5 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Abstención falsa | 0 % | 0 % | 0 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Abstención correcta | 100 % | 33.3 % | 60 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Explicaciones con citas válidas |  |  | 46/46 |
| Fichas documentales | `configs/documentary-evaluation-v1.json` | Consultas completas | 121/123 | reserva sin usar |  |
| Fichas documentales | `configs/documentary-evaluation-v1.json` | Citas válidas | 121/121 | reserva sin usar |  |
| Fichas documentales | `configs/documentary-evaluation-v1.json` | Campos de referencia exactos | 780/790 | reserva sin usar |  |

Detalle por componente: [morfología](#evaluación-del-analizador-morfológico), [términos](#evaluación-de-grupos-de-término), [Preguntar](#evaluación-de-la-consulta-con-evidencia), [fichas documentales](#fichas-documentales-preguntar).

## Evaluación del analizador morfológico

Analizador `nah-morph-1` · conjunto `morphology-gold-v1.json` · partición `all`. Generado por `make eval` (`python3 -m nahuatl_local.evaluate_all`).

### 1. Segmentación frente al conjunto de referencia

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

### 2. Cobertura del diccionario en el corpus clásico

135,288 palabras (26,396 formas distintas) de los pasajes `nci` de Axolotl.

| Medida | Palabras | Formas distintas |
|---|---:|---:|
| Coincidencia exacta con una forma del diccionario | 28.0% | 3.9% |
| Raíz enlazada por el analizador (diccionario o partícula) | 60.2% | 26.6% |
| Con al menos un afijo o enlace explicado | 86.4% | — |

### 3. Concordancia por raíz

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

### 4. Pistas de glosa del corpus paralelo frente a Molina

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

### Límites

- El conjunto de referencia es pequeño y lo redactó el equipo a partir de paradigmas de gramáticas; requiere revisión especializada.
- La partición `dev` se usó para ajustar costes. Tras la primera medición de `test` se corrigieron dos fallos generales (concordancia de categoría entre análisis y entrada; sustantivos breves registrados completos, como *atl*); la primera medición se conserva en `reports/morphology-evaluation-first-test-run.json`. Con 27 casos, un caso equivale a ~4 puntos.
- Molina (1571) no es un diccionario completo ni moderno: una pista correcta puede no aparecer en su definición.
- Ninguna cifra mide comprensión lectora ni calidad de traducción.

## Evaluación de grupos de término

Índice `terms-v1` · conjunto `term-groups-v1` · sin modelos. Regenerar: `make eval` (`python -m nahuatl_local.evaluate_all`).

Escrito antes de construir el índice de términos y antes de mirar sus resultados. Las expectativas vienen del conocimiento de la lengua y de los datos de entrada (nombres de glifos del diccionario y designaciones de Tlachia), no de la salida del índice. dev: términos vistos durante la exploración (los siete de la tarea y atl); test: escritos sin consultar la variación del archivo. No se ajusta el conjunto después de medir; una corrección se publica como v2.

| Partición | Términos | Consulta → grupo (top-1) | Mismo grupo | Grafías (cualquier nivel) | Grafías seguras | Glifos | Precisión grafías* | Precisión glifos* | Homógrafos separados |
|---|---|---|---|---|---|---|---|---|---|
| dev | 7 | 96.7% de 30 | 85.7% | 100.0% | 96.4% | 100.0% | 100.0% | 100.0% | 100.0% |
| test | 14 | 85.7% de 42 | 57.1% | 95.5% | 86.4% | 100.0% | 100.0% | 100.0% | None% |
| all | 21 | 90.3% de 72 | 66.7% | 98.0% | 92.0% | 100.0% | 100.0% | 100.0% | 100.0% |

\* Precisión sobre lo etiquetado: aciertos seguros frente a formas o glifos que el conjunto marca como no seguros y el índice presenta como seguros.

### Por término

| Término | Partición | Grupo | Consultas | Grafías | Glifos | Faltan | Presentadas como seguras sin serlo |
|---|---|---|---|---|---|---|---|
| calli | dev | calli (dictionary) | 5/5 | 7/7 | 3/3 | — | — |
| cualli | dev | cualli (dictionary) | 5/5 | 6/6 | 0/0 | — | — |
| tonatiuh | dev | tonatiuh (dictionary) | 4/4 | 2/2 | 2/2 | — | — |
| coatl | dev | coatl (dictionary) | 5/5 | 4/4 | 3/3 | — | — |
| cihuatl | dev | cihuatl (dictionary) | 5/5 | 5/5 | 1/1 | — | — |
| xochitl | dev | xochitl (dictionary) | 3/4 | 3/3 | 3/3 | — | — |
| atl | dev | atl (dictionary) | 2/2 | 1/1 | 2/2 | — | — |
| tlacatl | test | tlacatl (dictionary) | 3/3 | 3/3 | 1/1 | — | — |
| tochtli | test | tochtli (dictionary) | 2/3 | 1/1 | 2/2 | — | — |
| itzcuintli | test | itzcuintli (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| ehecatl | test | eecatl (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| mazatl | test | mazatl (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| ocelotl | test | ocelotl (dictionary) | 2/3 | 1/1 | 2/2 | — | — |
| cuauhtli | test | cuauhtli (dictionary) | 3/4 | 2/2 | 2/2 | — | — |
| tecpatl | test | tecpatl (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| cipactli | test | cipactli (dictionary) | 2/2 | 1/1 | 2/2 | — | — |
| ozomatli | test | ozomahtli (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| teotl | test | teotl (dictionary) | 2/3 | 2/3 | 0/0 | teteo | — |
| tlalli | test | tlalli (dictionary) | 3/3 | 3/3 | 0/0 | — | — |
| ilhuicatl | test | ilhuicaātl (dictionary) | 2/3 | 2/2 | 0/0 | — | — |
| metztli | test | metztli (dictionary) | 2/3 | 1/1 | 1/1 | — | — |

Consultas que no llevan al grupo esperado:

- xochitl: «sochitl» → sin grupo (—)
- tochtli: «toxtli» → temoxtli (misma raíz (sin esta grafía en el archivo))
- ocelotl: «jaguar» → oceloquichtli (la acepción dice «jaguar»)
- cuauhtli: «kuautli» → sin grupo (—)
- teotl: «dios» → dios (grafía del archivo (sin entrada en el diccionario))
- ilhuicatl: «ilhuicac» → ilhuicac (misma palabra)
- metztli: «mestli» → meztli (grafía del archivo (sin entrada en el diccionario))

## Evaluación de la consulta con evidencia

Sistema `evidence-root-v1` · conjunto `evidence-questions-v1` · partición `all`. Generado por `make eval` (`python3 -m nahuatl_local.evaluate_all`). Cero llamadas a modelos.

### 1. Resultado por partición

| Sistema | Partición | n | Entrada top‑1 | Entrada top‑3 | Con pasaje pertinente | Precisión de pasajes | Abstención falsa | Abstención correcta |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| exact_search | dev | 17 | 30% | 30% | 73.3% | 95.2% | 26.7% | 100% |
| exact_search | test | 32 | 42.3% | 42.3% | 75.9% | 84% | 24.1% | 33.3% |
| exact_search | all | 49 | 38.9% | 38.9% | 75% | 87.8% | 25% | 60% |
| evidence | dev | 17 | 90% | 90% | 100% | 99.2% | 0% | 100% |
| evidence | test | 32 | 92.3% | 92.3% | 100% | 96.4% | 0% | 33.3% |
| evidence | all | 49 | 91.7% | 91.7% | 100% | 97.5% | 0% | 60% |

### 2. Por tipo de consulta (todas las particiones)

| Tipo | n | Entrada top‑1 (base → evidencia) | Con pasaje pertinente (base → evidencia) |
|---|---:|---|---|
| abstain | 5 | — → — | — → — |
| inflected | 10 | 0% → 80% | 70% → 100% |
| question | 2 | 100% → 100% | 100% → 100% |
| spanish | 16 | 92.3% → 92.3% | 100% → 100% |
| variant | 16 | 0% → 100% | 50% → 100% |

### 3. Explicaciones con citas

Redactor `explain-cited-v1` (extractive): 46 de 46 explicaciones pasan la validación de citas (cada frase cita IDs de la evidencia y las formas entre «» aparecen en lo citado); 2.98 frases y 3.76 citas de media. Claude: not_run: usar --explain claude con credenciales (tiene costo); no se ejecutó en esta medición.

### 4. Fallos del sistema con evidencia

- `pájaro` (dev, spanish): entrada top‑1: acxoyatototl
- `atlan` (test, inflected): entrada top‑1: ninguna
- `michime` (test, inflected): entrada top‑1: ninguna
- `teléfono` (test, abstain): no se abstuvo — Etiqueta escrita antes de la primera corrida y conservada. El archivo sí traduce «teléfono» en pasajes de Morelos (huehcatlahtolaztli); mostrarlos no es un error.
- `automóvil` (test, abstain): no se abstuvo — Etiqueta escrita antes de la primera corrida y conservada. El archivo sí traduce «automóvil» (calmimilo, Morelos); mostrarlos no es un error.

### Límites

- Un pasaje es pertinente si la forma señalada (o, en la línea base, alguna palabra náhuatl del pasaje) contiene la raíz esperada según la clave laxa. Es una aproximación automática.
- El conjunto es pequeño y lo escribió el equipo técnico; las particiones separan desarrollo de prueba, no sustituyen la revisión de una persona experta.

## Fichas documentales (Preguntar)

Fichas `cards-v1` · batería `configs/documentary-evaluation-v1.json` (SHA256 estructurado `c6c26cbc3f1ef1d8…`). Se miden las 123 consultas textuales de desarrollo; la reserva (37 textuales y 15 visuales) no se usa, y las 52 observaciones visuales esperan derechos de imagen y un modelo con imágenes.

Una consulta está completa si las fichas devueltas contienen todos los campos de referencia (mismo valor, fila y archivo), sus fuentes y URLs, y todas las citas son válidas. Las referencias nunca entran en la consulta.

| Tarea | Consultas | Completas | Con fichas | Citas válidas | Campos exactos |
|---|---:|---:|---:|---:|---:|
| todas | 123 | 121 | 121 | 121/121 | 780/790 |
| comparison | 79 | 78 | 78 | 78/78 | 460/465 |
| lexical | 44 | 43 | 43 | 43/43 | 320/325 |

Consultas incompletas:

- `doc-textual-gloss-772588bdea8c94c2` (abstention, 0/5 campos): ¿Qué glosa histórica registra la ficha de A? Conserva todas las acepciones registradas y cita sus entradas.
- `doc-textual-spelling-772588bdea8c94c2` (abstention, 0/5 campos): Compara la escritura original y la normalización catalogada de A. ¿Coinciden y qué ID de acepción corresponde a cada ficha?

Límites: consultas parametrizadas sobre fichas conocidas; no miden comprensión, traducción ni reconocimiento de imágenes. Las referencias son documentales, sin revisión humana nueva.
