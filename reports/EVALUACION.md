# Evaluación de Amoxcalli

Una sola tabla, regenerable con `make eval` (`python -m nahuatl_local.evaluate_all`); `make check` vuelve a medir y falla si alguna cifra cambió sin regenerar este informe. Sin modelos ni red. Los conjuntos son pequeños y los escribió el equipo técnico: miden comportamiento técnico, no sustituyen la revisión de una persona experta.

`dev` se usa para ajustar; `test` solo para medir (la primera medición de cada conjunto de prueba, antes de corregir fallos, se conserva en `reports/*-first-test-run.*`). La batería documental se mide en desarrollo; su reserva no se usa.

| Componente | Conjunto | Medida | dev | test | total |
|---|---|---|---:|---:|---:|
| Morfología | `evaluation/morphology-gold-v1.json` | Segmentación exacta (top‑1) | 88 % | 89 % | 88 % |
| Morfología | `evaluation/morphology-gold-v1.json` | Segmentación en top‑3 | 100 % | 93 % | 96 % |
| Morfología | `evaluation/morphology-gold-v1.json` | Raíz correcta (top‑1) |  |  | 77 % |
| Morfología | `evaluation/morphology-gold-v2.json` | Segmentación y clase (top‑1; test ciego) | 89 % | 78 % |  |
| Morfología | Pasajes `nci` de Axolotl | Palabras con raíz enlazada |  |  | 60.4 % |
| Morfología | Molina (entradas evaluables) | Pistas de glosa, precisión@1 (IBM‑1) |  |  | 30 % |
| Índice de términos | `evaluation/term-groups-v1.json` | Consulta → grupo (top‑1) | 100 % | 90.5 % | 94.4 % |
| Índice de términos | `evaluation/term-groups-v1.json` | Grafías seguras | 85.7 % | 86.4 % | 86 % |
| Índice de términos | `evaluation/term-groups-v1.json` | Glifos | 100 % | 100 % | 100 % |
| Índice de términos | `evaluation/term-groups-v1.json` | Precisión de grafías (etiquetadas) | 100 % | 100 % | 100 % |
| Índice de términos | `evaluation/term-groups-v1.json` | Precisión de glifos (etiquetados) | 100 % | 100 % | 100 % |
| Grafías | `evaluation/spelling-search-v1.json` | Palabra buscada en top‑1 | 90.5 % | 94.2 % | 92.8 % |
| Grafías | `evaluation/spelling-search-v1.json` | Palabra buscada en top‑3 | 97.6 % | 97.1 % | 97.3 % |
| Grafías | `evaluation/spelling-search-v1.json` | Precisión del grafo de grafías | 100 % | 100 % | 100 % |
| Grafías | `evaluation/spelling-search-v1.json` | Cobertura del grafo de grafías | 86.7 % | 81.5 % | 83.3 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Entrada top‑1 | 90 % | 92.3 % | 91.7 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Entrada top‑3 | 90 % | 92.3 % | 91.7 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Con pasaje pertinente | 100 % | 100 % | 100 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Precisión de pasajes | 99.2 % | 96.3 % | 97.5 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Abstención falsa | 0 % | 0 % | 0 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Abstención correcta | 100 % | 33.3 % | 60 % |
| Preguntar | `evaluation/evidence-questions-v1.json` | Explicaciones con citas válidas |  |  | 46/46 |
| Preguntar por tema | `evaluation/topic-questions-v1.json` | Tema: elemento esperado en primer lugar | 100 % | 80 % |  |
| Preguntar por tema | `evaluation/topic-questions-v1.json` | Tema: elemento esperado entre los 5 primeros | 100 % | 95 % |  |
| Preguntar por tema | `evaluation/topic-questions-v1.json` | Tema: abstención correcta | 100 % | 100 % |  |
| Fichas documentales | `configs/documentary-evaluation-v1.json` | Consultas completas | 121/123 | reserva sin usar |  |
| Fichas documentales | `configs/documentary-evaluation-v1.json` | Citas válidas | 121/121 | reserva sin usar |  |
| Fichas documentales | `configs/documentary-evaluation-v1.json` | Campos de referencia exactos | 780/790 | reserva sin usar |  |

Detalle por componente: [morfología](#evaluación-del-analizador-morfológico), [términos](#evaluación-de-grupos-de-término), [grafías](#evaluación-del-buscador-de-grafías), [Preguntar](#evaluación-de-la-consulta-con-evidencia), [tema](#búsqueda-por-tema), [fichas documentales](#fichas-documentales-preguntar).

## Evaluación del analizador morfológico

Analizador `nah-morph-1` · conjunto `morphology-gold-v1.json` · partición `all`. Generado por `make eval` (`python3 -m nahuatl_local.evaluate_all`).

### 1. Segmentación frente al conjunto de referencia

| Sistema | n | Segmentación exacta (top‑1) | top‑1 dev / test | En top‑3 | Raíz correcta (top‑1) |
|---|---:|---:|---:|---:|---:|
| unsegmented_baseline | 52 | 0% | 0% / 0% | 0% | 0% |
| rules_only | 52 | 15% | 8% / 22% | 62% | 12% |
| rules+dictionary | 52 | 67% | 68% / 67% | 81% | 60% |
| rules+corpus_em | 52 | 85% | 88% / 82% | 98% | 75% |
| full (rules+dictionary+corpus_em) | 52 | 88% | 88% / 89% | 96% | 77% |

Errores del sistema completo:

- `tlachihualli` → `tlachihual-li` (esperado `tla-chihua-l-li`, dev)
- `mochiuh` → `mochi-uh` (esperado `mo-chiuh`, dev)
- `nitlacua` → `ni-tlacua` (esperado `ni-tla-cua`, dev)
- `quitoque` → `quito-que` (esperado `qu-ito-que`, test)
- `tlaqualli` → `tlaqual-li` (esperado `tla-qua-l-li`, test)
- `tetlazohtlaliztli` → `tetlazohtlaliz-tli` (esperado `te-tlazohtla-liz-tli`, test)

### 1b. Prueba v2 (`evaluation/morphology-gold-v2.json`)

dev = todo v1 + familias de error conocidas (se usa para ajustar); test = 91 formas nuevas escritas y congeladas antes de medir (sha256 en `evaluation/morphology-gold-v2.sha256`). Partículas y nombres cuentan solo si además el análisis tiene esa clase.

| Partición | n | Exacta (top‑1) | Palabras | Partículas | Nombres |
|---|---:|---:|---:|---:|---:|
| dev | 56 | 89% | 89% de 54 | 100% de 1 | 100% de 1 |
| test | 91 | 78% | 67% de 58 | 94% de 18 | 100% de 15 |

Nombres del test solo con la regla de mayúscula (sin la lista breve): 100% de 15.

Errores en test:

- `ticochizque` → `ti-cochi-zque` (esperado `ti-cochi-z-que`, word, base dictionary)
- `titlacua` → `ti-tlacua` (esperado `ti-tla-cua`, word, base dictionary)
- `quicaquia` → `qui-caquia` (esperado `qui-caqui-a`, word, base rules)
- `oquito` → `o-quito` (esperado `o-qu-ito`, word, base corpus)
- `motlalia` → `motla-lia` (esperado `mo-tlalia`, word, base dictionary)
- `tlaqua` → `tlaqua` (esperado `tla-qua`, word, base dictionary)
- `ninotlalia` → `ni-no-tla-lia` (esperado `ni-no-tlalia`, word, base corpus)
- `timotlalia` → `ti-motla-lia` (esperado `ti-mo-tlalia`, word, base dictionary)
- `teotl` → `teotl` (esperado `teo-tl`, word, base corpus)
- `atlan` → `atlan` (esperado `a-tlan`, word, base rules)
- `cuauhtli` → `cuauhtli` (esperado `cuauh-tli`, word, base corpus)
- `pilli` → `pi-l-li` (esperado `pil-li`, word, base corpus)
- `tlacuilo` → `tla-cui-lo` (esperado `tla-cuilo`, word, base corpus)
- `tlatolli` → `tlatol-li` (esperado `tlato-l-li`, word, base dictionary)
- `xochicuicatl` → `xochicuica-tl` (esperado `xochi-cuica-tl`, word, base dictionary_compound)
- `nopiltzin` → `no-piltzin` (esperado `no-pil-tzin`, word, base dictionary)
- `inahuac` → `i-nahua-c` (esperado `i-nahuac`, word, base dictionary)
- `icpac` → `icpa-c` (esperado `i-cpac`, word, base corpus)
- `ipan` → `ipan` (esperado `i-pan`, word, base dictionary)
- `tleica` → `tleica` (esperado `tleica`, particle, base rules)

### 2. Cobertura del diccionario en el corpus clásico

135,288 palabras (26,396 formas distintas) de los pasajes `nci` de Axolotl.

| Medida | Palabras | Formas distintas |
|---|---:|---:|
| Coincidencia exacta con una forma del diccionario | 28.0% | 3.9% |
| Raíz enlazada por el analizador (diccionario o partícula) | 60.4% | 26.5% |
| Con al menos un afijo o enlace explicado | 86.3% | — |

### 3. Concordancia por raíz

Para 1102 raíces del diccionario (≥4 fonemas) presentes en el corpus: la búsqueda por palabra exacta encuentra 10645 pasajes; el índice por raíz, 24648. 839 entradas ganan pasajes; 92 pierden alguno (1297 pasajes solo por búsqueda exacta).

Muestra para revisión humana de precisión: `reports/morphology-review/stem-hits-sample.csv`. Más pasajes no implica más aciertos: la muestra de revisión estima la precisión de los nuevos hallazgos.

| Entrada | Exacta | Por raíz |
|---|---:|---:|
| iipan | 0 | 1036 |
| Xiuitl | 176 | 1075 |
| ihuan, iuan | 172 | 972 |
| toca, tocatl | 11 | 683 |
| ihcuac | 105 | 597 |
| tlahtoa | 2 | 434 |
| ihtoa | 1 | 412 |
| mexihcatl | 0 | 308 |

### 4. Pistas de glosa del corpus paralelo frente a Molina

100 entradas con raíz presente en ≥2 pasajes. Acierto si una palabra propuesta (normalizada) aparece en la definición de Molina de esa entrada. Molina es independiente del corpus paralelo; la coincidencia ortográfica del s. XVI es aproximada.

| Método | Precisión@1 | Acierto en top‑3 |
|---|---:|---:|
| cooccurrence | 19% | 36% |
| dice | 23% | 36% |
| ibm1 | 30% | 37% |

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
| dev | 7 | 100.0% de 30 | 100.0% | 100.0% | 85.7% | 100.0% | 100.0% | 100.0% | 100.0% |
| test | 14 | 90.5% de 42 | 71.4% | 95.5% | 86.4% | 100.0% | 100.0% | 100.0% | None% |
| all | 21 | 94.4% de 72 | 81.0% | 98.0% | 86.0% | 100.0% | 100.0% | 100.0% | 100.0% |

\* Precisión sobre lo etiquetado: aciertos seguros frente a formas o glifos que el conjunto marca como no seguros y el índice presenta como seguros.

### Por término

| Término | Partición | Grupo | Consultas | Grafías | Glifos | Faltan | Presentadas como seguras sin serlo |
|---|---|---|---|---|---|---|---|
| calli | dev | calli (dictionary) | 5/5 | 7/7 | 3/3 | — | — |
| cualli | dev | cualli (dictionary) | 5/5 | 6/6 | 0/0 | — | — |
| tonatiuh | dev | tonatiuh (dictionary) | 4/4 | 2/2 | 2/2 | — | — |
| coatl | dev | coatl (dictionary) | 5/5 | 4/4 | 3/3 | — | — |
| cihuatl | dev | cihuatl (dictionary) | 5/5 | 5/5 | 1/1 | — | — |
| xochitl | dev | xochitl (dictionary) | 4/4 | 3/3 | 3/3 | — | — |
| atl | dev | atl (dictionary) | 2/2 | 1/1 | 2/2 | — | — |
| tlacatl | test | tlacatl (dictionary) | 3/3 | 3/3 | 1/1 | — | — |
| tochtli | test | tochtli (dictionary) | 2/3 | 1/1 | 2/2 | — | — |
| itzcuintli | test | itzcuintli (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| ehecatl | test | eecatl (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| mazatl | test | mazatl (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| ocelotl | test | ocelotl (dictionary) | 2/3 | 1/1 | 2/2 | — | — |
| cuauhtli | test | cuauhtli (dictionary) | 4/4 | 2/2 | 2/2 | — | — |
| tecpatl | test | tecpatl (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| cipactli | test | cipactli (dictionary) | 2/2 | 1/1 | 2/2 | — | — |
| ozomatli | test | ozomahtli (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| teotl | test | teotl (dictionary) | 2/3 | 2/3 | 0/0 | teteo | — |
| tlalli | test | tlalli (dictionary) | 3/3 | 3/3 | 0/0 | — | — |
| ilhuicatl | test | ilhuicaātl (dictionary) | 2/3 | 2/2 | 0/0 | — | — |
| metztli | test | metztli (dictionary) | 3/3 | 1/1 | 1/1 | — | — |

Consultas que no llevan al grupo esperado:

- tochtli: «toxtli» → temoxtli (misma raíz (sin esta grafía en el archivo))
- ocelotl: «jaguar» → oceloquichtli (la acepción dice «jaguar»)
- teotl: «dios» → dios (grafía del archivo (sin entrada en el diccionario))
- ilhuicatl: «ilhuicac» → ilhuicac (misma palabra)

## Evaluación del buscador de grafías

Buscador `spelling-v1` · conjunto `spelling-search-v1` (SHA-256 `e0769c941208…`) · sin modelos. Regenerar: `make eval`. Detalle: [docs/GRAFIAS.md](../docs/GRAFIAS.md).

El conjunto se escribió y congeló antes de construir el buscador (commit c079a11). Reglas activas: aligned, final_tl, z_tz.

| Partición | Consultas | Top-1 | Top-3 | Pares | Precisión del grafo | Cobertura del grafo | Uniones erróneas |
|---|---|---|---|---|---|---|---|
| dev | 42 | 90.5% | 97.6% | 21 | 100.0% | 86.7% | 0 |
| test | 69 | 94.2% | 97.1% | 33 | 100.0% | 81.5% | 0 |
| all | 111 | 92.8% | 97.3% | 54 | 100.0% | 83.3% | 0 |

### Por tipo de consulta

| Tipo | Consultas | Top-1 | Top-3 |
|---|---|---|---|
| colonial | 20 | 90.0% | 95.0% |
| known_failure | 13 | 92.3% | 100.0% |
| modern | 42 | 95.2% | 97.6% |
| negative | 5 | 100.0% | 100.0% |
| typo | 10 | 90.0% | 100.0% |
| variety | 21 | 90.5% | 95.2% |

### Consultas cuyo primer candidato no es la palabra buscada

- dev · «ilhuicac» → ilhuicac (pivot), ilhuicaātl (root), ilhuacac (edit); esperado ilhuicatl · top-3 sí
- dev · «iluikak» → ilhuicac (pivot), ilhuicaātl (root), ilhuacac (edit); esperado ilhuicatl · top-3 sí
- dev · «tonatih» → tonatih (pivot), tonatiuh (edit), tonalli (edit); esperado tonatiuh · top-3 sí
- dev · «kuouit» → kuouit (pivot), kuouat (edit), cueitl (edit); esperado cuahuitl/quahuitl
- test · «ejekatl» → ejekat (rule), eecatl (edit), aehecatl (edit); esperado ehecatl · top-3 sí
- test · «tlalticpac» → tlalli (pivot), taltikpak (edit), tlaticpac (edit); esperado tlalticpac
- test · «tlaltikpak» → tlalli (pivot), taltikpak (edit), tlaticpac (edit); esperado tlalticpac
- test · «sochimilco» → sochimilco (pivot), Xochimilco (rule), xochmilco (edit); esperado xochimilco · top-3 sí

### Pares mal asociados

- dev · huitzilopochtli / uizilopochtli: no unidas (misma palabra)
- dev · cuahuitl / kuouit: no unidas (misma palabra)
- test · tecuhtli / teuctli: no unidas (misma palabra)
- test · ehecatl / ejekat: no unidas (misma palabra)
- test · centli / sintli: no unidas (misma palabra)
- test · michin / michi: no unidas (misma palabra)
- test · xochitl / xochitli: no unidas (misma palabra)

## Evaluación de la consulta con evidencia

Sistema `evidence-root-v1` · conjunto `evidence-questions-v1` · partición `all`. Generado por `make eval` (`python3 -m nahuatl_local.evaluate_all`). Cero llamadas a modelos.

### 1. Resultado por partición

| Sistema | Partición | n | Entrada top‑1 | Entrada top‑3 | Con pasaje pertinente | Precisión de pasajes | Abstención falsa | Abstención correcta |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| exact_search | dev | 17 | 30% | 30% | 73.3% | 95.2% | 26.7% | 100% |
| exact_search | test | 32 | 42.3% | 42.3% | 75.9% | 84% | 24.1% | 33.3% |
| exact_search | all | 49 | 38.9% | 38.9% | 75% | 87.8% | 25% | 60% |
| evidence | dev | 17 | 90% | 90% | 100% | 99.2% | 0% | 100% |
| evidence | test | 32 | 92.3% | 92.3% | 100% | 96.3% | 0% | 33.3% |
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

Redactor `explain-cited-v1` (extractive): 46 de 46 explicaciones pasan la validación de citas (cada frase cita IDs de la evidencia y las formas entre «» aparecen en lo citado); 3.0 frases y 3.78 citas de media. Claude: not_run: usar --explain claude con credenciales (tiene costo); no se ejecutó en esta medición.

### 4. Fallos del sistema con evidencia

- `pájaro` (dev, spanish): entrada top‑1: acxoyatototl
- `atlan` (test, inflected): entrada top‑1: ninguna
- `michime` (test, inflected): entrada top‑1: ninguna
- `teléfono` (test, abstain): no se abstuvo — Etiqueta escrita antes de la primera corrida y conservada. El archivo sí traduce «teléfono» en pasajes de Morelos (huehcatlahtolaztli); mostrarlos no es un error.
- `automóvil` (test, abstain): no se abstuvo — Etiqueta escrita antes de la primera corrida y conservada. El archivo sí traduce «automóvil» (calmimilo, Morelos); mostrarlos no es un error.

### Límites

- Un pasaje es pertinente si la forma señalada (o, en la línea base, alguna palabra náhuatl del pasaje) contiene la raíz esperada según la clave laxa. Es una aproximación automática.
- El conjunto es pequeño y lo escribió el equipo técnico; las particiones separan desarrollo de prueba, no sustituyen la revisión de una persona experta.

### Búsqueda por tema

`topics-v1` · conjunto `topic-questions-v1` (escrito antes de construir la búsqueda). Acierto: un elemento esperado entre los 5 primeros.

| Partición | n | Primer lugar | Entre los 5 primeros | Abstención correcta |
|---|---:|---:|---:|---:|
| dev | 9 | 100.0 % | 100.0 % | 100.0 % |
| test | 21 | 80.0 % | 95.0 % | 100.0 % |

Fallos:

- `pájaros en la poesía` (test): lesson-draft:gen-cuicatl

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
