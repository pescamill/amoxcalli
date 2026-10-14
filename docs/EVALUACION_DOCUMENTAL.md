# Batería documental de Amoxcalli · v1

Se preparan referencias para comprobar consultas a campos públicos ya distribuidos. La batería no contiene respuestas de un modelo, juicios humanos nuevos ni resultados de recuperación. Sus preguntas parametrizadas sirven para contrastar fichas, paleografía, normalización, glosas, alineaciones y ausencias documentales. No miden comprensión humana ni generalización lingüística.

## Reproducción y alcance

```sh
.venv/bin/python -m nahuatl_local.documentary_evaluation
.venv/bin/python -m nahuatl_local.documentary_evaluation --check
.venv/bin/python -m unittest tests.test_documentary_evaluation tests.test_iteration -v
```

El módulo usa solamente stdlib y una lista explícita de fuentes públicas; no abre bases de datos, directorios privados, imágenes ni conexiones de red. Genera `configs/documentary-evaluation-v1.json` y `reports/documentary-evaluation-validation-v1.json`. Las mismas fuentes generan los mismos bytes. Antes de sustituir una batería diferente, guarda sus bytes originales en `reports/documentary-evaluation-backups/<sha256>.json`; una publicación editorial cuyo hash no coincide se rechaza.

Cada consulta tiene ID derivado de sus entidades y tarea, modalidad, pregunta, referencia estructurada y grupo. Cada campo referenciado conserva valor original, archivo, tabla, ID, nombre de campo, hash de fila y hash de archivo. Las fuentes y URLs se conservan por separado. `attributed_responsibility` identifica los autores/editoriales registrados: Molina/GDN, el corpus Axolotl y los responsables de cada estudio de Tlachia. El script ensambla claves documentales; no se atribuye su autoría histórica. `source_derived_not_human_validated` y la incertidumbre explícita impiden confundir transcripción con cotejo primario o análisis validado.

Las consultas léxicas distinguen glosa de traducción de un pasaje; las comparaciones conservan cada acepción y cada grafía catalogada. Las alineaciones citan original y español heredados, obra y variedad. Las observaciones contrastan denominación/lectura, componente/valor, cita/lectura, segmentación con marcas de duda, elementos no expresados y falta de vínculos léxicos. Una ausencia no es una equivalencia nueva ni prueba que algo falte en la lengua.

## Familias antes de partición

`partition` registra **todas** las familias de entradas admitidas, pasajes de las doce lecturas y entidades del catálogo, incluidas las no seleccionadas. Los recursos y miembros de cada familia se calculan antes de elegir consultas o asignar desarrollo/reserva:

- Léxico: ID de forma/acepción, misma acepción, entrada GDN declarada, escritura/normalización y aliases explícitos de formas. Se conservan distintas fuentes y acepciones; la agrupación solo evita fuga entre particiones. La reserva se fija por hash de familia (una de cada cinco candidatas), limitada a doce familias. Desarrollo incluye grupos ambiguos primero y después entradas individuales distribuidas por inicial. No se usan resultados ni modelos para elegirlos.
- Pasajes: ID CSV, original normalizado para detectar duplicados y obra completa. Reservar las dos últimas obras por título ordenado es una barrera más fuerte que reservar filas distintas del mismo libro. El ID original y el texto nunca se normalizan en las claves.
- Visual: manuscrito, lámina, zona, aparición, componente y URL literal compartida. Los componentes que se reutilizan conectan las láminas del mismo documento. Telleriano queda en desarrollo; Calpan y la sección Tianquiztenco de Matrícula de Huexotzinco quedan en reserva. No se afirma que Tianquiztenco sea otro manuscrito distinto de Huexotzinco.

La misma denominación aparece en manuscritos diferentes; eso no es la misma imagen ni una lectura equivalente. No se unen documentos por compartir un concepto. Las familias léxicas cuya escritura/normalización coincide con denominaciones pictográficas se excluyen de la selección textual para no reutilizar esas entradas como claves de ambos recorridos. La reserva visual evalúa futura comparación entre documentos conocidos, **no conceptos nunca vistos**. Tampoco acredita independencia de todas las relaciones históricas entre obras; ese cotejo requiere estudio.

El informe verifica intersecciones de grupos, entidades, registros realmente citados, URLs de imágenes y recursos completos de familias. Un ID de grupo inventado no basta: el validador reconstruye selección, referencias, atribución, condiciones y partición desde las fuentes. La v1 acepta exclusivamente esta receta; ampliaciones editoriales deben versionar la receta y mantener la historia. Las pruebas introducen variantes, copias de pasajes y recortes con imagen compartida para comprobar la unión antes del split.

## Permisos por uso

La instrucción humana de este ciclo autoriza preparación y validación local de consultas a datos públicos ya distribuidos. Las fichas léxicas conservan `public:true` y sus notas de transcripción breve; Axolotl mantiene la licencia declarada por el distribuidor y la auditoría pendiente por obra; el catálogo conserva su nota de índice de consulta con imágenes enlazadas, sin redistribución. Cada consulta reproduce las condiciones originales pertinentes en `source_conditions`.

`local_documentary_fields: authorized_local_scope` describe únicamente ese alcance operativo. **No concede una licencia legal nueva**. `evaluation:false`, `image_model_input:false`, `image_copy:false`, `external_send:false` y `training:false` se mantienen en la batería. Las observaciones visuales contienen campos y URLs de referencia: no son imágenes descargadas ni pruebas visuales ejecutadas. Procesarlas en un modelo visual, copiar imágenes, enviarlas a un servicio o entrenar requiere resolver las condiciones de cada documento y una ejecución autorizada; `image_evaluation_status: pending_rights_and_execution` lo hace explícito. El diagnóstico puede reconocer la preparación documental sin declarar habilitada una evaluación VLM.

La validación comprueba límites y condiciones exactamente; elevar esos permisos invalida la batería. No cambia ningún permiso de las fuentes, incluidos registros originales que tienen otras condiciones.

## Uso de desarrollo y reserva

`load_development()` devuelve copias exclusivamente del desarrollo y rechaza una batería obsoleta o alterada. No acepta un parámetro de reserva. La reserva se conserva en el artefacto auditable, pero no se proporciona al helper de ajuste. Quien diseñe recuperación debe usar este helper, fijar su método antes de la prueba final y registrar errores/abstenciones sin transformar generaciones en claves.

La batería cuenta 123 consultas textuales y 51 observaciones documentales visuales de desarrollo; la reserva contiene 37 textuales y 15 visuales. Es una reserva pequeña, fijada por evidencia y no por resultados. Las observaciones se distribuyen por lámina y por seis necesidades documentales; los casos de elementos no expresados dependen de que ese campo exista, sin rellenarlo. El conteo mide preparación, no suficiencia estadística.

La siguiente acción es implementar y medir recuperación textual sobre todos los casos textuales de desarrollo con estas referencias. No se ajusta el recuperador con la reserva. La comparación multimodal y la revisión humana siguen pendientes.
