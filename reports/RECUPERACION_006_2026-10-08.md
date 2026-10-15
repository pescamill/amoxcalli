# Recuperación documental · ciclo 006 · 8 de octubre de 2026

Preparación técnica local por GPT-6.1 Sol / high, dentro del ciclo autorizado de Amoxcalli. Se añadió una consulta pública de fichas y se midieron los **123 casos textuales de desarrollo**, sin entrenamiento, modelos, imágenes, red, publicación externa ni acceso del flujo de medición a la base privada de Voces. Los originales, las condiciones de fuentes y la reserva permanecen intactos. No se declara cotejo lingüístico ni revisión humana.

## Cambio y fuentes

`documentary_retrieval.py` es un recuperador stdlib separado del índice BM25/SFT histórico. Recibe registros públicos actuales y fuentes distribuidas; `search` recibe exclusivamente una cadena de consulta. Indexa 1317 registros públicos, los 16,111 pasajes de Axolotl y todas las tablas pictográficas (3 documentos, 13 láminas, 155 zonas, 152 elementos y 311 apariciones): 18,062 entidades de búsqueda. No importa la batería, su selección, query IDs ni claves; no selecciona corpus según referencias esperadas.

Las fuentes son los nueve bundles públicos seed/glifos/GDN/flor, publicaciones editoriales verificadas por manifiesto, `corpus/axolotl/axolotl.csv`, `configs/sources.json` y `corpus/pictography/catalog.json`. Los hashes exactos de fuentes, implementación, API, interfaz y guías están en [el informe JSON](documentary-retrieval-v1.json). Cada campo devuelve ID, valor original, ruta/tabla, hashes de fila/archivo y URL documentada. El original y la normalización se muestran por separado; cada acepción conserva su ID. Los pasajes conservan original, español, obra y variedad. La consulta de glifos devuelve metadatos y referencias, sin cargar imágenes.

La API `GET /api/documentary` comprueba `public_records()` cada petición y reconstruye el índice si cambian registros o archivos públicos. Excluye dependencias retiradas y puentes a acepciones ocultas. Una proyección pública que difiere del original lleva un namespace distinto y ningún falso hash de archivo; la UI la identifica como campo local y presenta su enlace como fuente relacionada. Rutas privadas, traversal y enlaces simbólicos se rechazan.

`#consultar` queda enlazado desde Diccionario, Archivo y Laboratorio. El formulario tiene etiqueta, estado accesible y resultados citados; permite volver a la palabra del Diccionario para guardar/repasar con el recorrido existente. Hay avisos sobre varias coincidencias, truncamiento, ausencia y límites de interpretación. No genera una traducción ni elige el sentido fuera de contexto.

## Método y cambios de desarrollo

El método se fijó antes de medir en [CONSULTA_DOCUMENTAL](../docs/CONSULTA_DOCUMENTAL.md): IDs completos, etiquetas/grafías completas y tokens con ponderación por frecuencia, hasta 20 resultados y 1.000 caracteres; originales intactos. No hay parser de plantillas de la batería, generación ni juez de modelo.

La primera corrida y su engine se conservan en [experimento inicial](documentary-retrieval-experiments/initial/preparation.json); el hash reconstruido de ese snapshot coincide con el engine registrado entonces. Una comprobación independiente con «agua» mostró que una forma no incluía la etiqueta española explícita de su acepción vinculada. Se añadieron esos labels/aliases para recuperar la forma con su original, sin inferir sinónimos. Se separó la validez de citas devueltas de la cobertura de todas las URLs requeridas; dos respuestas parciales tienen citas válidas y siguen incompletas. Las corridas intermedias se respaldan por SHA256. Las correcciones finales de UI hacen visibles los campos locales y el regreso al Diccionario. Se volvió a medir tras congelar implementación, UI y guías; no se ajustó el filtro para eliminar los fallos A/Y.

El evaluador obtiene solamente desarrollo por `load_development(modality='textual')`. La reserva participa exclusivamente en validación estructural/fingerprint; ninguna clave reservada se usa para ranking, ajuste o medición. Fingerprint congelado: `f2b2996e86d3595ff117b014962340eafbed0e894cc73e9b14f56a7008a09fb4`. `correct_source` exige **todos** los IDs/campos esperados, sus valores/hashes y fuentes/URLs; compartir Molina o GDN no basta. `supported_citations` verifica exactamente los campos/URLs devueltos. Los expected target IDs figuran solo en el evaluador para auditoría.

## Resultados medidos

| Medida | Resultado |
|---|---:|
| Consultas textuales de desarrollo | 123 |
| Completas: todos los campos/fuentes y citas válidas | 119 / 123 |
| Correct source completo | 119 / 123 |
| Citas devueltas sustentadas | 121 / 123 |
| Cobertura con resultados | 121 / 123 |
| Coincidencias relevantes en campos requeridos | 121 / 123 |
| Abstenciones | 2 / 123 |
| Campos requeridos exactos recuperados | 840 / 860 |
| Construcción del índice con tracing | 6.042268 s |
| Consultas acumuladas | 0.884299 s |
| Consulta media / máxima | 0.007189 / 0.075467 s |
| Total de medición, incluida preparación/cotejo | 7.724964 s |
| Pico Python trazado | 121,586,015 bytes |

Los tiempos usan `perf_counter` real. La memoria usa `tracemalloc` desde la construcción del índice y durante consultas/cotejo: excluye fuentes ya cargadas, preparación de batería previa, memoria nativa y memoria total del proceso. El tracing afecta latencia; estas cifras corresponden a esa ejecución, no a un límite universal ni a una comparación con generación. Repetir medición cambia tiempos; verificar el mismo informe y repetir diagnóstico preserva bytes.

Los cuatro fallos son deterministas: dos preguntas extensas sobre **A** abstienen porque A se filtra como palabra funcional; dos comparaciones/glosas **Titi / Y** recuperan Titi y omiten Y por el mismo filtro. La consulta aislada de A funciona. Los cuatro errores y los 20 campos ausentes permanecen en JSON. No se añadieron respuestas ni vínculos por inferencia.

## Validación y estado

- 30 pruebas dirigidas iniciales pasan; después del cierre, 21 pruebas de recuperador/gate pasan, incluida falsificación de campos y duplicación de consultas.
- Suite completa: **224 pruebas, OK, con 1 fallo esperado histórico**. [Registro](tests-all-documentary-006.txt).
- **10 grupos DOM/HTTP** pasan en UI final: campos originales, distintas acepciones, pasajes citados, regreso al Diccionario, proyecciones locales, etiquetas/estado, abstención, escaping y progreso preservado. [Registro](platform-ui-documentary-css-final-006.txt).
- Offline no guarda corpus, perfiles, aportaciones ni peticiones externas. [Registro](offline-documentary-006.txt).
- El primer intento de bind de una prueba HTTP fue bloqueado por sandbox; la repetición aprobada automáticamente usa puerto temporal y base sintética y pasa. [Registro](tests-documentary-retrieval-http-retry-006.txt).
- El validador final reproduce respuestas deterministas y referencias; booleanos inventados o texto generado no completan la tarea técnica. El manifiesto incorpora código/docreferencias usados y rechaza symlinks.

La repetición del diagnóstico contra el mismo informe produce **inventory.json, inventory.md, queue.json y state.json idénticos en bytes**. Se comprobaron los prefijos de historia, runs, notas y snapshots, las decisiones y todas las fuentes congeladas de 005. [Evidencia de repetición y conservación](iteration-repeat-retrieval-006-2026-10-08.json).

`iteration-006` conserva el respaldo [state-before-006](iterations/state-before-006.json), las tareas anteriores, decisiones, notas, snapshots y su historia. La recuperación sale de la cola actual como preparación técnica medida; su estado histórico sigue abierto y recibe una nota local, sin inventar revisión humana. La cola queda en **67 tareas abiertas: 66 humanas y 1 técnica**, comparación del Laboratorio. Se conservan 12 lecturas, 48 pasajes, 575 acepciones, 578 formas, 311 apariciones y 9 puentes; originales, permisos y pesos no se modificaron. El agente de implementación no detuvo ni reinició el servidor habitual; el coordinador realiza la comprobación final de navegador con su configuración previa.

## Corrección tras revisión real en navegador

El coordinador detectó desbordamiento horizontal material en `#consultar/agua`: CSP bloqueaba los estilos inline y PRE conservaba `white-space:pre`. Se retiraron los estilos inline y se añadió `.card.documentary-hit pre` a `/corpus.css`, con `pre-wrap` y corte de cadenas largas. El stylesheet entra en hashes de medición y diagnóstico. La prueba DOM final exige estilo calculado `pre-wrap`/`anywhere` y ausencia de inline; los diez grupos vuelven a pasar. La comprobación real posterior del coordinador confirmó `document.clientWidth = document.scrollWidth = 1265` y PRE con `pre-wrap`/`anywhere`, además del regreso al Diccionario sin cambios de progreso. No se cambió el ranking ni se reinició el servidor habitual; la medición posterior conserva 119/123 completos y los cuatro fallos. Se refrescaron las métricas de este informe y la repetición de 006; la suite 224 no se repitió, pues se comprobaron UI, replay y gate afectados. [Pruebas críticas posteriores](tests-documentary-css-final-006.txt).

## Límites y siguiente ciclo

Estas preguntas parametrizadas contienen grafías o IDs; el resultado mide consulta documental de fichas conocidas, no comprensión general de náhuatl ni fidelidad de traducción nueva. La consulta puede devolver resultados relacionados sin cubrir la petición completa, y se trunca en 20. La presencia de una fuente no autoriza entrenamiento, procesamiento/copia de imágenes ni envío externo. Cotejo primario, permisos visuales, revisión lingüística y ensayos con personas siguen pendientes.

Siguiente prioridad: mostrar en Laboratorio la recuperación medida junto al estado real del modelo textual y candidato multimodal, con ejecución reproducible o ausencia explícita, costes, fallos y permisos. No iniciar entrenamiento ni convertir registros de catálogo en juicios humanos.
