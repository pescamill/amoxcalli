# Laboratorio del LLM

La navegación principal abre **Laboratorio** en `http://127.0.0.1:8766/#modelos`. Tiene tres pestañas: [Probar](http://127.0.0.1:8766/#modelos/probar), [Datos de entrenamiento](http://127.0.0.1:8766/#modelos/datos) y [Modelo y progreso](http://127.0.0.1:8766/#modelos/progreso).

## Probar: elegir el método

La opción inicial **Buscar ejemplos con fuente** consulta pasajes existentes en español y náhuatl, sin ejecutar el LLM. **Generar un borrador con el LLM** usa Qwen3-0.6B y el adaptador LoRA local, todavía poco fiable; muestra método, tiempo y límites de la salida. **Consultar reglas léxicas limitadas** conserva los patrones locales acotados. El resultado del generador se exporta como ficha para revisión, nunca como respuesta correcta.

La antigua opción «Añadir pasajes» se presenta dentro de **Experimento con ejemplos de referencia**: el buscador elige hasta dos pares relacionados y los copia delante de la frase en el mensaje enviado al modelo. **Ver qué ejemplos recibirá** permite inspeccionarlos antes de generar. Esto es RAG: cambia el contexto de esa petición, no los pesos. Nuestro adaptador se entrenó sin ese formato, por lo que no se promete una mejora. La evidencia aparece separada del borrador.

El modelo recibe texto, no imágenes glíficas. Las lecturas guiadas conservan ejemplos del corpus y claves editoriales; guardar palabras, aportar pares y abrir el laboratorio no inicia entrenamiento.

## Datos: español y náhuatl lado a lado

El visor permite buscar en ambos idiomas, filtrar obra, paginar 20 pares y descargar la página con procedencia. Distingue:

| Conjunto | Pares | Qué significa |
|---|---:|---|
| Recorridos por el adaptador | 650 | 400 del piloto + 250 de continuación, identificados mediante orden y cursor del checkpoint |
| Preparación histórica de entrenamiento | 2.248 | Incluye 1.759 pares admisibles a 192 tokens; no todos fueron recorridos |
| Entrenamiento actual | 2.161 | Preparación `nah-ortho-1`; los pesos actuales no se entrenaron con ella |
| Validación actual reservada | 2.049 | Evaluación, excluida de nuevas aportaciones al entrenamiento |
| Prueba actual reservada | 1.252 | Evaluación reservada |

Los JSONL históricos se reconstruyeron desde el CSV original y sus tres SHA256 coinciden exactamente con `outputs/continued-unseen/automation.json`. La referencia y los IDs recorridos están en `data/training-reference/continued-unseen/`; se verifican al arrancar. El script de reconstrucción no modifica el corpus preparado ni los pesos:

```bash
.venv/bin/python scripts/reconstruct-training-reference.py --output /tmp/referencia-historica-nueva
```

Necesita el tokenizador y checkpoint locales para recuperar el orden. El visor usa la referencia incluida y no requiere PyTorch ni cargar pesos. Las alineaciones originales siguen pendientes de revisión filológica propia; que un par se haya usado para entrenar no certifica su traducción.

## Añadir pares

Con un perfil de **Aportar** en la misma sesión puedes guardar un par español/náhuatl clásico o importar CSV UTF-8 usando la plantilla descargable. Cada par conserva texto, obra, localizador, fuente y licencia/permiso. El CSV admite comas y saltos de línea entre comillas, hasta 200 filas y 500 KB. Los errores se indican por fila. Cada envío requiere permiso para compartir, revisión y eventual entrenamiento.

Las propuestas se guardan privadas en SQLite. Puedes ver y retirar las tuyas. No se publican ni modifican los conjuntos de entrenamiento automáticamente. Se bloquean duplicados y obras reservadas. Una persona responsable debe revisar traducción y permisos; la aceptación sigue en terminal, con motivo y revisor:

```bash
python3 -m nahuatl_local.training_data review ID_DE_PROPUESTA \
  --reviewer 'Nombre del responsable' --reason 'Cotejo y permisos documentados' \
  --rights-checked --linguistic-checked
python3 -m nahuatl_local.training_data export --output data/pares-revisados-nuevos.csv
python3 -m nahuatl_local.curate data/pares-revisados-nuevos.csv \
  --base data/prepared --output data/curated-nuevo
```

Usa rutas nuevas: los comandos rechazan sobrescritura. El navegador descarga solo tus pares aceptados; el responsable puede exportar todos los aceptados desde terminal. `curate` conserva validación y prueba byte por byte y escribe otra preparación. Entrenar es un paso posterior explícito; ver [MEJORAR.md](MEJORAR.md).

## Modelo y progreso: resultados y procedencia

`GET /api/laboratory` resume informes sin cargar los pesos. Muestra disponibilidad detectada al arrancar, adaptador de referencia/seleccionado, corrida, curva, métricas y hashes. No es un monitor de procesos ni un porcentaje de competencia lingüística.

La referencia es `outputs/continued-unseen/run/best`: 400 pasos heredados y 250 adicionales. La curva de continuación contiene 0/100/200/250; NLL 3,5783 → 3,5302 sobre 128 ejemplos. La comparación de generación usa 12 frases fijas de validación: chrF++ 22,58 → 27,96 y repetición 0 → 0,028. Se comprueban IDs, hash, split, firma y formato antes de marcar una comparación como controlada. La salida registrada «La casa y la flor.» → `Yn otlacuia yn otlacuia.` muestra un fallo real, sin simular una generación nueva.

Los hashes actuales difieren de aquella corrida: esas métricas no evalúan la preparación actual. El informe histórico de recuperación usa 100 frases, chrF++ 16,0123, sin LLM; muestras y preparaciones distintas impiden comparación directa con el modelo o con la batería documental actual. Los informes y resumen de visita son descargables mediante una lista cerrada, sin exponer perfiles ni checkpoints binarios.

No hubo nuevo entrenamiento con estos cambios. Para mejorar el LLM hace falta revisar ejemplos y comparar recuperación, base y adaptador sobre la misma validación actual antes de otra corrida. La ampliación del diccionario conserva `rights.training=false` y no alimenta los pesos.


## Comparación documental vigente

**Modelo y progreso** empieza con tres métodos sobre la batería documental v1: recuperación local medida; Qwen3-0.6B + LoRA sin ejecutar sobre estos casos; y Qwen3-VL-4B-Instruct como candidato sin descarga ni ejecución. El candidato figura en [ROADMAP.md](ROADMAP.md); su ficha no prueba competencia en náhuatl. Solo la recuperación tiene resultados y costes medidos. Tiempo, memoria, puntuación y coste monetario de los modelos figuran **Sin medir**, con `null` en JSON; tampoco se inventa un coste monetario para recuperación.

La recuperación conserva **119/123 completas**, **121/123 con resultados**, **121/121 respuestas con citas válidas**, **840/860 campos requeridos exactos**, **2 parciales y 2 abstenciones**. Una parcial puede citar campos válidos y seguir sin cubrir toda su referencia. Los cuatro fallos de desarrollo se enlazan a Consultar fichas para reproducir la pregunta. Es una evaluación de consultas parametrizadas a registros conocidos, no de comprensión general, traducción, reconocimiento de imágenes ni utilidad para personas.

Hay 123 consultas textuales y 51 observaciones documentales visuales de desarrollo; la recuperación solo usa las 123 textuales. La reserva de 37 textuales y 15 visuales se conserva sin evaluar ni usar para elegir cambios. Los modelos sin ejecutar quedan vinculados a la misma batería objetivo; no reciben puntuaciones y no se afirma que un método supera a otro. Los resultados históricos del adaptador se muestran en otro apartado.

`tracemalloc` registra memoria Python trazada durante construcción y consultas, con las fuentes ya cargadas antes de comenzar. No incluye esas fuentes previas, memoria nativa ni RSS del proceso. `perf_counter` registra construcción, acumulado/media/máximo de consultas y total; el trazado puede alterar los tiempos y cada corrida depende del equipo. Refrescar la medición tras cambios de hashes conserva algoritmo y batería, pero genera costes nuevos. No constituye una corrida de modelo.

`reports/documentary-laboratory-v1.json` incorpora hash literal y fingerprint estructurado de batería, hashes públicos actuales, métricas y coste copiados del informe de recuperación validado, estados/razones de cada método, fallos y condiciones. `documentary_laboratory.validate_report` reproduce la recuperación y exige contrato completo idéntico al derivado del informe actual; un hash de cualquier archivo o tres booleanos no completan el hito. Rechaza cifras inventadas, rutas privadas, métodos ausentes, permisos elevados e informes obsoletos.

```sh
make check     # informes medidos vigentes, sin escribir
make reports   # tras cambiar ranking, datos, batería o evaluador: medir una vez y derivar el Lab
```

`GET /api/laboratory` añade la comparación pública sin cargar pesos. Las rutas cerradas `/api/laboratory/reports/documentary-comparison` y `/api/laboratory/reports/documentary-retrieval` descargan proyecciones con agregados, costes, hashes y fallos observados; **excluyen referencias esperadas, claves y consultas de reserva**. El informe completo permanece como artefacto auditable local. No hay una ruta de descarga de la batería en el laboratorio. Si cambia una entrada medida, la comparación se marca no disponible hasta medir de nuevo.

El alcance de esta batería conserva `training:false`, `evaluation:false`, `image_model_input:false`, `image_copy:false` y `external_send:false`; la autorización local de campos públicos no crea una licencia nueva ni modifica las condiciones originales de cada fuente. Derechos de imágenes, revisión de sentido y pruebas con personas siguen pendientes. No se entrenó, descargó pesos, evaluó imágenes, contactó a nadie ni publicó externamente.

## Vigencia: qué invalida un resultado

Los `input_hashes` del informe de recuperación cubren solo las dependencias de sus respuestas, citas y evaluación (`documentary_retrieval_evaluation.IMPLEMENTATION` y `documentary_evaluation.FIXED`); el informe Lab añade la validación de la batería. **La presentación no tiene hashes**: un cambio de `platform.py`, `platform_web/*` o de las pruebas DOM se comprueba con `make test-ui` y no exige regenerar ningún informe. Ante cambios en ranking, datos, fuentes, batería o evaluador, `make reports` mide una vez y deriva el Lab; la validación reproduce el resultado real, de modo que no admite respuestas inventadas.

## Preparación del candidato con imágenes

En `#modelos/progreso`, el visor muestra estado `not_run` de `Qwen/Qwen3-VL-4B-Instruct` y preflight local. `python3 -m nahuatl_local.visual_preparation` lee versiones de paquetes y el registro literal de configuraciones mediante AST, sin importar librerías del modelo ni abrir pesos. Una arquitectura declarada en el registro no prueba carga, inferencia, soporte de hardware ni que quepa en memoria. No se actualizan dependencias automáticamente.

`GET /api/laboratory` incluye únicamente estado/conteos de esta preparación. **`GET /api/laboratory/visual-preparation`** es un visor explícito para inspección humana de las consultas **visuales documentales de desarrollo**, validado por `load_development(modality='visual')` y reconstrucción. No acepta parámetros de split/ruta ni ejecución POST. Las referencias quedan fuera de las proyecciones públicas de comparación/medición y del estado general descargable. No se expone ninguna referencia de reserva.

Los selectores de obra/pregunta conservan los campos literales esperados, códigos/componentes cuando están citados, fuentes, derechos y hashes en «Campos de referencia», cerrado inicialmente. La pregunta y entrada propuesta mantienen esos campos separados: no se construye un prompt con claves. Se ofrecen enlaces a ficha/imagen; no hay imágenes cargadas automáticamente, copiadas ni enviadas a un modelo.

Estos 51 casos **no son un benchmark de reconocimiento de píxeles ni una prueba image-only**. Citas y otros campos de catálogo pueden no encontrarse en la imagen; son referencias derivadas de fuente, sin validación humana nueva. La batería conserva `training:false`, `evaluation:false` e `image_model_input:false`. Ante fuentes o permisos alterados, no se muestran casos. Una ejecución posterior requiere autorización de fase, derechos de datos, pesos/runtime compatible y una prueba mínima de carga/inferencia sobre una imagen admitida, con salida y costes reales; hace falta otra referencia adecuada para evaluar reconocimiento visual.
