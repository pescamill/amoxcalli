# Primera prueba local de un modelo con imágenes

Propuesta concreta, 12 de octubre de 2026. **Preparada; no autorizada ni ejecutada.** La fase actual de [trabajo autónomo](TRABAJO_AUTONOMO.md) excluye la descarga y el entrenamiento de un modelo grande. Esta propuesta pide ampliar el alcance únicamente a una prueba local de inferencia.

## Qué probar

Una conversión de Qwen3-VL-4B-Instruct a MLX de cuatro bits, en un entorno independiente del modelo textual actual. La [ficha del publicador](https://huggingface.co/mlx-community/Qwen3-VL-4B-Instruct-4bit) declara una conversión del [modelo original de Qwen](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct), aproximadamente 3,09 GB y licencia Apache-2.0. Es una distribución derivada; comprobar revisión, archivos y condiciones antes de descargar. No se presupone competencia en náhuatl.

El equipo tiene 16 GiB de RAM, diez núcleos y arquitectura arm64, comprobados mediante metadatos del sistema. No se ha medido el consumo ni la velocidad de este modelo. La instalación textual tiene Transformers 4.51.3, sin la arquitectura `qwen3_vl` en su registro; MLX/MLX-VLM no están instalados. Se conservará la instalación actual.

## Alcance y límites propuestos

- Entorno separado y directorio de modelo nuevo; no actualizar la instalación textual ni sus adaptadores.
- Hasta **4 GB de descarga de pesos**; comprobar tamaños anunciados y fijar una revisión antes de comenzar. Si supera ese límite, detener la descarga propuesta.
- Sin API de pago, publicación externa, entrenamiento ni modificación de corpus.
- Una imagen técnica propia de formas geométricas, creada para la prueba, y una salida de hasta 100 tokens. No incorporarla al diccionario ni presentarla como un glifo histórico.
- No procesar imágenes de Tlachia/GDN con esta autorización: sus referencias actuales conservan permisos pendientes para entrada a modelos. Seleccionar material histórico admisible en una etapa posterior.
- Limitar la ejecución a cinco minutos y cancelarla si falla la carga o falta memoria; no ampliar contexto ni repetir hasta obtener una respuesta favorable.

## Qué se entregará

Resultado real y sin corregir, versión/revisión del modelo y runtime, hash de la imagen propia, duración, memoria observada cuando pueda medirse y errores. La prueba comprueba que imagen y texto llegan a un modelo local. No demuestra lectura de glifos ni traducción del náhuatl.

Después, con material histórico permitido y referencias revisadas, comparar imagen sola, recuperación documental y modelo con contexto sobre los mismos casos. Las 51 consultas documentales actuales permiten examinar fichas y sus campos; las citas bibliográficas de una ficha no se deducen de los píxeles. No reutilizar esos campos como respuestas ocultas dentro del prompt ni usar la reserva para elegir mejoras.
