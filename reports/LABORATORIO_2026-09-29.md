# Laboratorio y continuidad del proyecto

Entrega del 29 de septiembre de 2026. Se guardó el estado interno en [PROGRESO_INTERNO.md](../docs/PROGRESO_INTERNO.md) y se actualizaron README, guías de plataforma/webapp, estado del modelo, dirección educativa, instrucciones de mejora/entrenamiento y model card. Los informes y model cards de corridas anteriores se conservan como registros históricos.

## Interfaz

Laboratorio es una sección de la navegación principal (`#modelos`). Explica base, LoRA, preparación, inferencia y recuperación. Muestra disponibilidad local, pasos registrados, curva NLL con tabla accesible, métricas de generación, hashes de datos, salida histórica, informes descargables y próximos experimentos. Los controles distinguen generación del LLM, reglas locales y consulta léxica. La búsqueda de ejemplos continúa independiente; los pasajes recuperados se muestran separados del borrador.

`nahuatl_local/laboratory.py` resume informes conocidos sin cargar pesos. `/api/laboratory` obtiene métricas y hashes por visita; `/api/laboratory/reports/{id}` sirve una lista cerrada de informes JSON. No hay acceso genérico a archivos, estados binarios, perfiles ni aportaciones. Un adaptador seleccionado distinto se distingue de la referencia histórica; una muestra o formato distinto no se marca como comparación controlada. Los informes incompletos no acreditan comparabilidad.

## Estado del modelo

Qwen3-0.6B + LoRA continúa instalado, con el adaptador `outputs/continued-unseen/run/best`. No se entrenaron nuevos pesos. El piloto de 400 pasos y la continuación de 250 corresponden a datos anteriores; la última corrida conserva estado de pausa por presupuesto. NLL de continuación: 3,5783 → 3,5302; generación en 12 frases de validación: chrF++ 22,58 → 27,96, repetición 0 → 0,028.

La preparación actual tiene hashes distintos. Las instrucciones de mejora ahora explican que esa corrida no puede reanudarse ni heredar el cursor sobre estos archivos: para usarlos, crear otra ejecución inicializada desde los pesos, después de revisar/evaluar los datos. Solo se reevaluó recuperación sobre la preparación actual (100 frases, chrF++ 16,0123), sin ejecutar el generador en un benchmark actual.

## Comprobación

- 139 pruebas Python: OK, con 1 fallo esperado de una regla ortográfica deshabilitada. [Salida](tests-laboratorio-2026-09-29.txt).
- Tras el último ajuste que exige campos completos en los informes de comparación, las 4 pruebas específicas del laboratorio volvieron a pasar.
- Prueba DOM: aprendizaje, guardado/repaso, búsqueda, variantes, aportación/retiro, fuentes y laboratorio. Sin errores JavaScript. [Salida](platform-ui-laboratorio-2026-09-29.txt).
- Navegador real: disponibilidad en servidor principal, curva y tabla, navegación interna, controles sin modelo y pantalla de 390 px. El documento no desborda horizontalmente; la navegación principal se adapta en varias filas.
- Se ejecutó una generación real local, sin RAG, para «La casa y la flor.». Produjo `Yn otlacuia yn otlacuia.`; la pantalla indicó método LLM, repetición detectada, borrador pendiente y pasajes separados. Los 1,10 s mostrados fueron tiempo de generación de esta llamada, no un benchmark de velocidad ni una promesa de tiempo total. No se guardó como material correcto ni se añadió al entrenamiento.

El laboratorio describe progreso experimental, no competencia lingüística validada ni entrenamiento en vivo. La revisión de ejemplos, evaluación común de base/adaptador/recuperación y cotejo lingüístico siguen siendo los siguientes pasos sustantivos. La actualización no modifica el corpus preparado, etiquetas pendientes, pesos ni aportaciones.
