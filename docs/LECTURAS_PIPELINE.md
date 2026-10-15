# Ampliar lecturas con fuentes y recetas

`nahuatl_local.lesson_builder` ensambla selecciones editoriales de Axolotl. Usa el archivo local y el diccionario distribuido, sin red ni LLM. La receta conserva decisiones explícitas sobre objetivo, pasajes, palabras y contexto; el script automatiza lo repetible.

## Receta y propuesta

La [receta lecturas-002](../configs/learning-expansion-2026-09-30.json) contiene tres lecturas y dos aclaraciones de lecturas existentes. Una receta nueva tiene:

- Un ID estable nuevo, título, objetivo, duración y acepciones de consulta.
- Un glifo de portada perteneciente a una acepción objetivo.
- Cuatro IDs de pasajes nuevos del archivo clásico, en orden de lectura.
- Contextos y anotaciones de citas exactas, con acepción, tipo de relación y referencia visual explícita.
- Un hueco de palabra completa y dos distractores conocidos del diccionario por ejemplo.
- Dos consejos breves que aclaren el contexto o una confusión probable.

El script recupera cada par original, calcula SHA256 de `nah + "\0" + es`, genera las tres opciones y su clave a partir del hueco exacto, y valida las dependencias. Rechaza pasajes ya seleccionados, palabras/distractores desconocidos, portadas de otra acepción, referencias ausentes y anotaciones equivocadas. Una coincidencia de letras dentro de otra palabra no pasa como palabra completa. Las formas con análisis pendiente necesitan una relación editorial explícita; no se crea morfología ni una definición automática.

```bash
.venv/bin/python -m nahuatl_local.lesson_builder \
  --config configs/mi-receta-lecturas.json \
  --output editorial/mi-propuesta-lecturas.json
```

La salida reúne el nuevo archivo de aprendizaje, hashes de base/receta y un resumen de preservación. No publica hasta añadir `--apply`. `--base` permite evaluar una instantánea histórica o un borrador; la incorporación solo se permite sobre el archivo canónico `corpus/learning-v1.json`.

## Aclaraciones y progreso

`lesson_updates` admite rótulos, objetivo, consejos y notas/relaciones de anotaciones existentes. No altera los pasajes ni los ejercicios. Una aclaración incrementa la versión de contenido y conserva `practice_version`: las claves y el progreso de práctica siguen siendo los mismos. Si cambian pasajes o claves en otra edición, hay que incrementar también la edición de práctica.

La app muestra la forma del pasaje y la entrada de consulta en lugares separados. Una comparación temática no aparece como traducción completa de un compuesto. Las referencias contextuales mantienen su nota y sus fuentes. Los consejos se muestran antes del fragmento; el lector completo conserva los originales y sus contextos.

## Incorporar y comprobar

```bash
.venv/bin/python -m nahuatl_local.lesson_builder \
  --config configs/mi-receta-lecturas.json \
  --output editorial/mi-propuesta-lecturas.json --apply
```

Detener el servidor para incorporar y reiniciarlo después: carga las lecciones al arrancar. El script guarda un respaldo en `reports/learning-before-ID/learning-v1.json` y reemplaza el archivo canónico de forma atómica. Repetir una propuesta ya incorporada devuelve `already_published`. Un archivo de salida con otro contenido requiere una versión nueva.

Después:

```bash
.venv/bin/python -m nahuatl_local.lesson_audit \
  --output reports/learning-audit-MI_ID
```

La auditoría regenera todos los paquetes y reabre decisiones cuya evidencia cambió, conservando el archivo de decisiones humanas. Al cambiar lecciones, los lotes de diccionario preparados anteriormente quedan obsoletos por hash: preparar otro ID con el [pipeline editorial](EDITORIAL_PIPELINE.md).

La interfaz cuenta los ejemplos de cada lectura y del lector completo dinámicamente. El ensamblador propone cuatro por defecto; la UI también se verificó con dos.

## Estado de la primera expansión

Se añadieron agua/tierra, flores/cantos y aves: 3 recorridos / 12 pasajes. La app reúne 6 recorridos / 24 pasajes de 6 obras. Las 12 selecciones y claves previas se conservaron, junto con la práctica guardada.

Son lecturas editoriales con revisión primaria y lingüística pendiente. El mecanismo valida citas y referencias; no acredita interpretación semántica, análisis gramatical ni eficacia con principiantes. Los permisos de entrenamiento y las reservas de evaluación siguen separados.


## Comprensión y palabras para explorar

Las recetas pueden incluir `comprehension` (`kind=meaning`, pregunta, opciones, índice de respuesta y explicación) y `explore_words`. La respuesta correcta debe ser una cita literal de la traducción española del registro; las formas para explorar deben aparecer en su texto náhuatl. Esto comprueba procedencia, no calidad pedagógica o lingüística. Para añadirlos a un ejemplo existente, usar `lesson_updates[].example_updates[]` con `archive_id`; no se reemplazan ni el pasaje ni la clave de reconocimiento. La receta [reading-context-2026-10-07](../configs/reading-context-2026-10-07.json) muestra cuatro ejemplos de Aves. Se conserva `practice_version=1`; la interfaz registra la comprensión aparte y mantiene el reconocimiento previo.
