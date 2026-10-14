# Estado real del LLM

Actualización: 12 de octubre de 2026. El modelo textual permanece disponible en el Laboratorio de la navegación principal. La base, el adaptador y las dependencias están instalados en este equipo; consultar el laboratorio no carga pesos ni inicia entrenamiento.

## Estado de la ruta con imágenes

**Todavía no hay un nuevo modelo multimodal ejecutado o entrenado.** El candidato es Qwen3-VL-4B-Instruct. Laboratorio → Modelo y progreso permite inspeccionar 51 consultas documentales visuales de desarrollo, con fuentes y campos de referencia separados de la entrada propuesta; la reserva queda fuera del visor. Consultar una ficha y sus enlaces no equivale a reconocer un glifo desde sus píxeles.

El preflight lee metadatos y el registro literal de arquitecturas sin importar librerías del modelo: Torch 2.9.0, Transformers 4.51.3 y PEFT 0.15.2; `qwen3_vl` no está registrado y MLX/MLX-VLM no están instalados. No se han medido memoria, latencia ni competencia lingüística. Los permisos actuales siguen sin admitir imágenes históricas como entrada al modelo ni para entrenamiento.

La [prueba local preparada](PRUEBA_VISUAL_LOCAL.md) propone una conversión de cuatro bits, entorno independiente, hasta 4 GB de pesos y una imagen técnica propia, sin entrenamiento ni imágenes del catálogo. Está pendiente de autorización para ampliar la fase. [Cambios y pruebas de esta iteración](../reports/PREPARACION_VISUAL_016_2026-10-12.md).

## Integración textual comprobada el 29 de septiembre

La webapp usa Qwen3-0.6B con el adaptador LoRA ya entrenado en `outputs/continued-unseen/run/best`. No se entrenaron pesos nuevos durante esta integración. JEV está retirado.

Se restauraron la base y las dependencias y se ejecutó el endpoint HTTP real `/api/compose`, usando CPU y cuatro hilos. No se simularon respuestas ni se llamó a una API externa.

| Prueba | Tiempo total en este equipo | Observación |
|---|---:|---|
| «La casa y la flor.», con dos pasajes en la instrucción | 37.0 s | Salida larga y repetitiva; alcanzó el límite de generación |
| Misma entrada, sin pasajes dentro de la instrucción | 16.35 s | Salida breve repetida; tampoco demuestra traducción fiel |

Informes completos: `reports/webapp-model-rag-probe.json` y `reports/webapp-model-smoke.json`. Estos tiempos incluyen carga y dependen del equipo; no son una promesa de rendimiento. La prueba comprueba integración, no calidad lingüística.

El adaptador original se entrenó con instrucciones de traducción sin contexto RAG. Por eso el modo normal genera con aquel formato y muestra los pasajes recuperados por separado; los controles avanzados permiten probar la inyección de contexto. La webapp marca toda generación como borrador y señala repeticiones exactas detectadas o límites de longitud. Una salida sin esas señales tampoco queda validada.

## Qué falta para un traductor fiable

1. Revisar alineaciones y reunir ejemplos diversos por obra y fenómeno lingüístico, conservando permisos.
2. Separar pruebas por obra/hablante antes de entrenar; evitar que las mismas frases entren por recuperación o por entrenamiento a la evaluación.
3. Afinar con el mismo formato que usará la app. Si se desea RAG, entrenar y comparar con contextos pertinentes y distractores.
4. Comparar siempre con el checkpoint anterior en frases inéditas, midiendo repetición, omisiones, negación, persona y tiempo, además de chrF.
5. Revisar una muestra con especialistas y hablantes de las variedades pertinentes. El corpus histórico y las variedades actuales necesitan evaluaciones separadas.

El flujo de continuación permanece en `scripts/autotrain.sh` y `docs/MEJORAR.md`; con la preparación actual hay que crear otra ejecución, porque los hashes cambiaron. Una interfaz funcional y un corpus más grande no corrigen por sí solos los pesos del modelo.


## Progreso mostrado en la aplicación

El adaptador conserva el piloto de 400 pasos y 250 adicionales. La continuación registrada el 23 de septiembre está pausada por presupuesto: NLL 3,5783 → 3,5302 sobre 128 ejemplos; chrF++ 22,58 → 27,96 sobre 12 frases de validación, con repetición 0 → 0,028. No hubo entrenamiento nuevo al crear la experiencia educativa o el laboratorio.

Los hashes actuales de entrenamiento y validación difieren de los usados por esos pesos. La preparación actual contiene 5.462 pares (2.161/2.049/1.252), normalización `nah-ortho-1`. Solo se evaluó de nuevo la recuperación: 100 frases de validación, chrF++ 16,0123, sin LLM. La interfaz conserva la procedencia y evita presentar esas cifras como comparables.

[LABORATORIO.md](LABORATORIO.md) describe los informes y controles; [PROGRESO_INTERNO.md](PROGRESO_INTERNO.md) guarda el estado del proyecto y próximos pasos.


## Visor de pares y propuestas · 29 de septiembre de 2026

El laboratorio separa Probar, Datos de entrenamiento y Modelo y progreso. La referencia histórica se recuperó exactamente por SHA256: 2.248 pares preparados, 1.759 admisibles a 192 tokens, 650 recorridos por el adaptador. El visor muestra español/náhuatl lado a lado; la preparación actual permanece identificada como otro conjunto. Las propuestas manuales/CSV necesitan revisión y exportación a otra preparación antes de entrenar. El diccionario ganó 499 entradas por extracción determinista de GDN/Molina, sin llamadas al LLM y con permiso de entrenamiento desactivado. No se modificaron los pesos. Detalles: [LABORATORIO.md](LABORATORIO.md) y [estado interno](PROGRESO_INTERNO.md).
