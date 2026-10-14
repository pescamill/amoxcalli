# Diagnóstico reproducible y tareas de iteración

El comando trabaja con las fuentes públicas distribuidas y una base `CorpusStore` temporal. Reutiliza `Learning` y `lesson_audit`; no abre la base privada de Voces, modifica el corpus, publica contenido, usa modelos ni consulta la red.

```sh
.venv/bin/python -m nahuatl_local.iteration \
  --output reports/iterations/iteration-001 \
  --state reports/iterations/state.json
```

Genera `inventory.json`, `inventory.md` y `queue.json`. El estado separado conserva tareas, notas, decisiones, snapshots e historia, incluidos hallazgos que desaparecieron. Una repetición con las mismas fuentes y estado produce los mismos bytes. Para otro ciclo, cambiar solo el directorio de salida y conservar `--state`.

El informe calcula lecturas, pasajes, registros públicos por tipo, documentos pictográficos, denominaciones, elementos, apariciones y enlaces léxicos. Enumera destinos ausentes, imágenes o significados no registrados, elementos sin apariciones, apariciones sin citas/componentes y componentes sin valores. Estas ausencias describen el índice: no exigen inventar vínculos ni completar campos sin fuente.

La cola diferencia `technical` y `human`. Reutiliza los hallazgos de `lesson_audit` y preserva las decisiones de `editorial/lesson-decisions.json` sin escribir ese archivo. Importa el estado previo solamente si corresponde al fingerprint del hallazgo; conserva también la decisión original. Los hashes de evidencia importada se observan ahora, sin afirmar que existían en la fecha de la revisión previa. Una tarea humana puede registrar preparación o bloqueo técnico; resolverla no certifica revisión lingüística ni ensayo con personas.

La meta documental propuesta es 300 apariciones, tomada de `TRABAJO_AUTONOMO`. Por debajo aparece una tarea técnica para preparar un candidato con `pictography_pipeline`. No publica ni completa cuotas automáticamente. `--occurrence-target N` ajusta esa propuesta; cero desactiva dicha tarea.

Cada tarea tiene ID estable y fingerprint del hallazgo, categoría y fuentes pertinentes. Los cambios de fuente reabren una decisión previa. Los cambios o retiradas de archivos usados como evidencia también la reabren, conservando decisión, notas y snapshots. Los hashes generales permiten detectar un informe anterior obsoleto, incluso si cambió una fuente que no altera un hallazgo. Son hashes locales: no comprueban que una página remota siga igual.

Para registrar una decisión explícita, preparar un JSON con el ID y fingerprint actuales de `queue.json`:

```json
{
  "id": "ID-DE-QUEUE",
  "fingerprint": "FINGERPRINT-DE-QUEUE",
  "status": "in_progress",
  "reviewer": "Responsable y alcance de la decisión",
  "date": "2026-10-07",
  "evidence": ["reports/informe-existente.md"],
  "resolution": "Trabajo realizado y aspectos aún pendientes",
  "notes": "Nota que se conserva"
}
```

```sh
.venv/bin/python -m nahuatl_local.iteration \
  --output reports/iterations/iteration-002 \
  --state reports/iterations/state.json \
  --record-decision reports/iterations/decision.json
```

Los estados admitidos son `open`, `in_progress`, `blocked`, `deferred` y `resolved`. Registrar una decisión exige responsable, fecha ISO, resolución, fingerprint actual y al menos un archivo de evidencia existente. Las rutas de evidencia son relativas al proyecto, dentro de directorios públicos; no se siguen URLs, `..` ni enlaces simbólicos. No usar el estado como evidencia de su propia decisión. El diagnóstico no declara decisiones humanas automáticamente.

`notes` de cada tarea puede ampliarse directamente en el estado; se conserva en las ejecuciones siguientes. El historial de decisiones debe ampliarse mediante el comando. Un estado inválido provoca un error antes de escribir. Las salidas dentro del proyecto deben quedar en `reports/`; se rechazan destinos que puedan sobrescribir fuentes o datos privados. Si cambia una fuente durante el diagnóstico, el comando aborta para permitir una nueva corrida coherente.

```sh
.venv/bin/python -m unittest tests.test_iteration tests.test_lesson_audit -v
```

## Lecturas, recuperación y evaluación documental

La meta por defecto es **12 lecturas editoriales**. `--lesson-target N` la ajusta; cero desactiva ampliación. `learning-next-source-backed-readings` existe solamente mientras el conteo es menor que la meta. Alcanzar la cantidad retira esa tarea técnica de la cola actual; su historia permanece y no resuelve ningún hallazgo de revisión especializada. `iteration-003` registra 12 lecturas / 48 pasajes tras el lote [lecturas-003](../reports/LECTURAS_003_2026-10-07.md).

Los artefactos públicos permiten comprobar los hitos restantes. El ciclo 005 preparó la batería y su informe de validación: **123 consultas textuales y 51 observaciones documentales visuales de desarrollo; 37 textuales y 15 visuales de reserva**. Recuperación y laboratorio disponen desde los ciclos 006/007 de informes documentales; solo la recuperación fue medida sobre esta batería. Los benchmarks históricos de traducción train-only siguen siendo experimentos diferentes. La lectura didáctica tampoco cambia splits ni permisos de entrenamiento.

| Artefacto | Tarea técnica mientras falte evidencia actual |
|---|---|
| `configs/documentary-evaluation-v1.json` + `reports/documentary-evaluation-validation-v1.json` | `evaluation-documentary-development-reserve` |
| `reports/documentary-retrieval-v1.json` | `retrieval-documentary-baseline` |
| `reports/documentary-laboratory-v1.json` | `laboratory-documentary-multimodal-comparison` |

El diagnóstico admite solamente JSON objeto con `schema_version: 1`. Una ausencia, JSON malformado, hash obsoleto o contrato incompleto deja la preparación pendiente. La evidencia completa retira la tarea técnica actual, preservando snapshots/decisiones/notas; no inventa una decisión `resolved`. Si la evidencia deja de ser válida, la tarea reaparece. El conteo no mide calidad ni implica que un método ganó.

### Contrato de batería

La [batería documental v1](EVALUACION_DOCUMENTAL.md) usa `queries` con ID único, entidades, grupo, modalidad, split, tarea, pregunta y referencia **estructurada**. Cada campo citado tiene archivo/tabla/ID/campo/valor literal, hashes de fila y archivo; las fuentes, URLs y responsables originales se declaran por separado. `reference_authority: documentary` y `review_status: source_derived_not_human_validated` no representan un juicio humano nuevo. No se aceptan referencias generadas ni cadenas genéricas.

`source_hashes` comprende las fuentes públicas explícitas, módulo y política de receta. El diagnóstico reconstruye el artefacto con `documentary_evaluation.validate` y exige el informe de validación persistido idéntico al recalculado. Conteos, `group_id` inventados o hashes de un documento cualquiera no acreditan preparación. Si faltan claves, cambian valores originales, se altera la partición o se elevan permisos, la tarea permanece abierta.

La preparación requiere al menos 100 consultas textuales y 50 observaciones documentales visuales de desarrollo, más reserva textual y visual. Las familias se calculan desde acepciones, entradas, variantes, obras/pasajes y manuscritos/láminas/recortes/URLs compartidos **antes** de escoger consultas y splits. El informe verifica intersecciones reales de entidades, registros citados, imágenes y recursos de familias. Es una reserva documental pequeña, sin uso para elegir cambios; no se declara independencia de conceptos ni comprensión humana.

El alcance autorizado es consulta y validación local de campos públicos ya distribuidos (`local_documentary_fields: authorized_local_scope`), con las condiciones originales registradas. `rights.evaluation: false`, `training: false`, `image_model_input: false`, `image_copy: false` y `external_send: false` impiden convertir esa preparación en permiso general. Las URLs sirven como referencias para futuras comparaciones; **ninguna imagen fue procesada por un modelo**. El diagnóstico informa `scope: local_documentary_fields_only` y `visual_model_evaluation_enabled: false`. La tarea humana de derechos continúa pendiente.

### Contrato de recuperación

El informe incluye `method: public_documentary_retrieval`, `evaluation_fingerprint` calculado con la codificación histórica (JSON con claves ordenadas y originales Unicode) del objeto completo de batería, `input_hashes` públicos actuales y `elapsed_seconds` medidos. `results` tiene exactamente una fila por consulta textual de desarrollo, cubriendo tanto `lexical` como `comparison`. Cada fila contiene `query_id`, `source_ids` como lista de IDs citados, los booleanos `correct_source`, `supported_citations`, `abstained` y `reference_checked: true`. Las claves resultan del cotejo con la referencia independiente, nunca de una segunda respuesta del modelo. Un resultado falso y una abstención son mediciones válidas que deben conservarse; completar este informe no declara rendimiento aceptable. La reserva no interviene en el ajuste.

Desde el ciclo 006, `documentary_retrieval_evaluation.validate_report` reproduce la recuperación determinista y coteja cada campo, URL y hash con las fuentes actuales. El informe también conserva la respuesta estructurada, IDs/campos requeridos, ausencias, configuración, métricas separadas y coste real. Compartir una fuente general o declarar booleanos no completa el hito. `source_manifest` incorpora implementación, API, UI y guía de consulta, y rechaza enlaces simbólicos en sus rutas. Desde 014, el manifiesto de medición incluye únicamente recuperador, store/variantes, datos/fuentes, batería y receta/evaluador. UI, navegación, CSS y guías de proceso permanecen en el diagnóstico, pero no invalidan la medición. La evidencia de presentación mantiene sus hashes por separado. El diagnóstico sobre un informe fijo permanece reproducible. Véase [Consulta documental](CONSULTA_DOCUMENTAL.md).

### Contrato de laboratorio

El informe comparte `evaluation_fingerprint`, `input_hashes` y `display_evidence` (rutas públicas con hashes de la comprobación de su presentación en la app). `runs` declara exactamente tres métodos: `retrieval`, `textual_model` y `multimodal_candidate`. Cada uno tiene `status: measured` y `report_hashes` de su informe medido, o `status: not_run` y `reason` explícita. La recuperación debe figurar como medida, pues su informe es requisito previo. Los informes medidos deben conservar resultados, fallos, coste y condiciones de reproducción; la comprobación estructural de hashes no acredita su calidad. El estado textual previo no se convierte en ejecución multimodal. Este contrato permite presentar honestamente ausencias; no autoriza entrenamiento, descargas grandes o publicación externa.


Desde el ciclo 007, el gate de Laboratorio usa `documentary_laboratory.validate_report`, deriva exactamente resultados, denominadores, fallos y costes del informe actual de recuperación y exige evidencia DOM/HTTP completa vinculada a la proyección pública y fuentes vigentes. Los dos modelos siguen `not_run`, con razón explícita, métricas/coste `null` y sin informes medidos. La preparación técnica de esta presentación puede retirar la tarea sin declarar comparativa de rendimiento, evaluación visual ni revisión humana. Los manifiestos excluyen el propio informe Lab y la evidencia de display para evitar ciclos; el diagnóstico sí observa ambos archivos y la implementación de UI. Véase [Laboratorio](LABORATORIO.md).
