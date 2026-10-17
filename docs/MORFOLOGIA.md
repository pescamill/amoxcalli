# Analizar cualquier palabra · morfología, concordancia por raíz y glosa interlineal

Actualización: 14 de octubre de 2026. [Arquitectura (EN)](ARCHITECTURE.md) · [Evaluación](../reports/EVALUACION.md#evaluación-del-analizador-morfológico)

## Para qué sirve

En una lectura, cualquier palabra se puede pulsar, no solo las anotadas. La aplicación propone su segmentación (*ni-qu-itta*: yo · lo · ver), enlaza la raíz con el diccionario cuando la entrada existe, muestra otros pasajes con la misma raíz aunque cambien prefijos o sufijos (*calli, ical, nocal, calco…*) y, si la raíz no está en el diccionario, ofrece pistas de traducción tomadas de los pares alineados, siempre con los pasajes que las sustentan.

«Mostrar glosa interlineal» presenta el pasaje palabra por palabra: forma de la fuente · segmentación · etiquetas · glosa. En el Diccionario, una búsqueda sin resultados (*nocalco*) sugiere su análisis (*no-cal-co* → *calli · casa*).

Las anotaciones editoriales conservan prioridad y los ejercicios de completar no se modifican, para no revelar respuestas.

## Qué afirma y qué no

Cada análisis declara su base:

| Base | Significado |
| --- | --- |
| Raíz en el diccionario | La raíz coincide con una entrada compatible (sustantivo / verbo) del diccionario del proyecto. |
| Partícula frecuente | Forma entera de la tabla gramatical del analizador (*in, auh, ihuan, oncan*…). |
| Raíz recurrente en el archivo | La raíz no está en el diccionario, pero se repite en otras palabras del corpus clásico. |
| Solo reglas | Segmentación posible sin apoyo léxico; tómala como conjetura. |

Las pistas «≈» son asociaciones estadísticas (IBM‑1) entre una raíz y las palabras españolas de los mismos pasajes; se muestran solo con tres o más pasajes de apoyo. No son acepciones ni traducciones. El análisis no usa un LLM ni modifica el diccionario, las lecturas o el entrenamiento.

## Cómo funciona, en breve

1. Una **clave fonémica** neutraliza la variación colonial (*yhuan/ihuan/iuan*, *xihuitl/xiuitl*, *iquac/ihcuac*) y conserva, para cada sonido, el tramo de la grafía original; por eso la segmentación se muestra con la escritura de la fuente.
2. Una **gramática de posiciones** genera candidatos con prefijos (poseedor; antecesivo, sujeto, direccional, objeto, reflexivo) y sufijos (absolutivo, poseído, plural, relacionales, derivación, tiempo) y restricciones de alomorfía.
3. La **puntuación** combina evidencia del diccionario (una raíz apoyada solo en entradas de Wiktionary, sin fuente lexicográfica revisada, pesa menos: `SECONDARY_PENALTY`) con concordancia de categoría, frecuencia de la raíz en el corpus (EM duro sobre 26 mil formas), preferencia nominal/verbal aprendida y un coste por afijo.

Detalles, cifras y comparación con líneas base: [ARCHITECTURE.md](ARCHITECTURE.md) y [la evaluación](../reports/EVALUACION.md#evaluación-del-analizador-morfológico) (`make eval`).

## Uso

```bash
python3 -m nahuatl_local.morphology niquitta nocalco omoteneuh   # análisis en terminal
python3 -m nahuatl_local.morphology_evaluation                   # regenera el informe
python3 -m unittest tests.test_morphology
```

API local: `GET /api/word?w=nocal` y `GET /api/gloss?id=axolotl-05338` (o `?text=`). El primer arranque prepara `data/derived/` (~45 s, en segundo plano); después tarda unos segundos. Esos archivos derivados no se versionan: se regeneran si cambian el diccionario, el corpus o el analizador.

## Revisión pendiente y cómo ayudar

- El conjunto de referencia (`evaluation/morphology-gold-v1.json`, 52 formas) y las tablas de afijos y partículas (`nahuatl_local/morphology.py`) fueron redactados por el equipo a partir de gramáticas de referencia; necesitan revisión especializada.
- `reports/morphology-review/stem-hits-sample.csv` contiene 60 pasajes encontrados por raíz y no por palabra exacta; marca en la última columna si comparten lexema.
- No se modelan reduplicación, longitud vocálica, pretéritos irregulares ni compuestos de más de dos raíces. Los homógrafos (*toa* en *tlatoa* / *itoa*) aparecen como alternativas.
- Pregunta abierta: `nah-ortho-1` compara `ç` como `tz`; GDN normaliza la `ç` de Molina como `z` (*çan → zan*). El analizador usa `ç = s`.
