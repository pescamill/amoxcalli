# Iteración autónoma de Amoxcalli

Plan de trabajo autorizado el 7 de octubre de 2026. Mantiene el [propósito didáctico](PROPOSITO.md) y añade una ruta experimental de texto e imágenes. Las metas siguientes son criterios de trabajo, no resultados ya alcanzados.

## Corrección de metodología · 12 de octubre de 2026

El usuario pidió acelerar después de varias entregas de infraestructura sin un cierre claro de Aves. Cada iteración debe terminar un cambio útil para quien aprende, o corregir un fallo demostrado que lo impida. No abrir otro ciclo para documentar, congelar o volver a verificar el mismo cambio. Las pruebas pertinentes y un registro breve forman parte de la entrega; su cantidad no es una medida de avance didáctico.

Separar tres estados: **disponible para estudiar**, **revisado lingüísticamente** y **probado con lectores**. Aves está disponible para estudio con cuatro pasajes, ocho ejercicios y una comparación final; los otros dos estados siguen pendientes. Conservar fuentes e incertidumbre permite ofrecer esa versión acotada sin afirmar revisión especializada. Los pendientes humanos no bloquean toda mejora local del producto.

Trabajar sobre una lectura completa y cerrar su recorrido antes de crear herramientas generales nuevas. Automatizar lotes cuando haya una necesidad demostrada. Comprobar solo lo afectado por el cambio; repetir una prueba únicamente si cambió su entrada, falló o queda una duda concreta. Un cambio de interfaz requiere comprobación de interfaz; uno de datos, ranking o referencia requiere evaluación correspondiente. Cambiar una guía de trabajo no requiere volver a medir recuperación ni renovar evidencia visual.

Los expedientes conservan la versión que se examinó. No crear otro paquete de Aves por cambios de navegación o de metodología si sus originales y ejercicios siguen iguales. Distinguir contenido preservado de metadatos históricos; preparar otro expediente cuando cambie el material que necesita revisar una persona. Mantener un siguiente paso concreto, sin repetir en cada ejecución que falta revisión humana ni aumentar contenido por cuota.

## Dos mecanismos complementarios

Un objetivo persistente permite trabajar durante una sesión hasta cumplir criterios verificables. Una tarea recurrente vuelve a este chat y retoma el estado en ejecuciones posteriores. En ambos casos el trabajo debe quedar en archivos del proyecto, con resultados y pendientes explícitos.

La documentación oficial describe [Goal mode](https://learn.chatgpt.com/docs/long-running-work) y [tareas programadas](https://learn.chatgpt.com/docs/automations?surface=app). Para operar sobre esta carpeta local, el equipo debe estar encendido y la aplicación abierta. La programación está sujeta a disponibilidad, permisos y límites de uso; no implica ejecución continua ni un presupuesto ilimitado.

El usuario autorizó comenzar de inmediato y aumentar la frecuencia, con **GPT-6.1 Sol / high**. Se activó un objetivo persistente en este chat y la automatización `iterar-amoxcalli-gpt-6-1-sol-high`, cada **30 minutos**. El seguimiento retoma este chat y delega la implementación a un único subagente con `model="gpt-6.1-sol"`, `reasoning_effort="high"` y `fork_turns="none"`, transmitiendo el contexto explícitamente. El coordinador verifica el resultado. La herramienta de seguimiento no permite fijar modelo/razonamiento directamente; estos parámetros se aplican al agente de implementación. No se presupone el modelo del coordinador.

La cadencia permite hasta 48 activaciones programadas diarias, sujetas a disponibilidad y límites. Si hay trabajo activo se continúa ese trabajo, sin iniciar otro escritor. No representa 48 entregas garantizadas ni una frecuencia máxima certificada por la plataforma. Los experimentos con el modelo de Amoxcalli siguen siendo un flujo distinto del modelo del agente programador.

## Qué significa una primera versión considerable

| Hito | Resultado verificable |
|---|---|
| Diagnóstico | Inventario calculado, conexiones faltantes, excepciones y prioridades; cada ejecución deja el siguiente paso concreto |
| Aprendizaje | Conservar las seis lecturas actuales; preparar otras seis con pasajes de fuente, formas comprobadas y ejercicios sustentados, diferenciando preparación, publicación y revisión especializada |
| Consulta pictográfica | Llegar a 300 apariciones documentales, distribuidas entre al menos tres conjuntos, con códigos, contexto y atribución; las asociaciones sin evidencia permanecen pendientes |
| Asistente con fuentes | Resolver consultas léxicas y comparaciones de fichas mediante recuperación verificable, con enlaces; medir esta base antes de añadir generación |
| Evaluación | Preparar una batería de desarrollo de 100 consultas textuales y 50 visuales, con procedencia, incertidumbre y responsable del tipo de referencia; reservar además una prueba final independiente |
| Laboratorio | Mostrar comparaciones reproducibles entre recuperación, modelo textual y candidato multimodal; registrar fallos y coste medido, aunque el modelo nuevo no supere la base |
| Comprensión real | Revisar al menos una lectura con una persona competente y probarla con principiantes; este hito requiere participación humana y no puede declararse completo con pruebas de software |

Las cantidades organizan el trabajo y pueden ajustarse con el usuario. No son criterios suficientes de calidad lingüística. El agente puede completar la preparación técnica y editorial mientras espera revisión humana; debe mantener ambos estados separados.

## Ciclo de cada ejecución

1. Leer este documento, PROPOSITO, PROGRESO_INTERNO y el último informe de iteración. Inspeccionar los cambios actuales y respetar los trabajos existentes.
2. Escoger una carencia demostrable: navegación, conexión con evidencia, extracción, ejercicio, recuperación o evaluación. Priorizar una mejora que ayude a comprender o comprobar una fuente.
3. Preparar un cambio acotado o un lote. Reutilizar cachés y scripts; evitar investigar cada fila con un LLM.
4. Comparar con el estado anterior. Mantener IDs, originales, grafías, incertidumbre, permisos y progreso. Una hipótesis nueva exige evidencia nueva.
5. Ejecutar las comprobaciones pertinentes. Corregir fallos reproducibles; después de tres intentos fallidos sobre el mismo problema, registrar el bloqueo y pasar a una tarea independiente si existe.
6. Publicar localmente solo contenido admitido por las validaciones y su nivel editorial. No convertir una transcripción de catálogo en revisión especializada. Conservar respaldos.
7. Registrar en un informe nuevo: problema, cambios, fuentes, pruebas, métricas, límites, bloqueos y siguiente tarea. Actualizar PROGRESO_INTERNO sin borrar la historia.

Una ejecución debe terminar con un resultado revisable. Cuando los hitos técnicos estén cubiertos, las ejecuciones posteriores verifican cambios externos relevantes y pendientes de revisión; no añaden contenido por llenar una cuota ni repiten experimentos idénticos.

## Autocorrección con referencias independientes

Las respuestas del modelo son candidatos, nunca claves nuevas. Las referencias provienen de datos documentales o juicios humanos identificados. Una segunda llamada al mismo modelo puede señalar problemas, pero no acredita fidelidad lingüística.

El conjunto de desarrollo se usa para comparar hipótesis. La prueba final no se usa para elegir prompts, datos, parámetros o adaptadores. Agrupar variantes de una entrada, versiones de un mismo pasaje y recortes de una misma lámina antes de separar conjuntos. Para medir generalización visual, no basta con reservar una copia distinta de la misma imagen.

Medir por tarea: recuperación de la ficha pertinente, precisión de citas, distinción entre denominación y lectura, respeto de incertidumbre, omisiones, repeticiones y tiempo/memoria. En traducción añadir revisión de sentido, persona, número, negación, posesión, tiempo/aspecto y valencia. chrF y pérdida son medidas auxiliares. Medir también cobertura y abstenciones para que responder menos no aparente una mejora general.

Una mejora del modelo necesita superar la referencia previa en desarrollo, conservar las comprobaciones de regresión y pasar una revisión acorde con su uso. Si tres experimentos comparables no mejoran, cambiar la hipótesis o trabajar en los datos; no continuar épocas sin una razón nueva.

## GDN y un modelo con imágenes

El [GDN](https://gdn.iib.unam.mx/presentacion) reúne diccionarios de distintas épocas y regiones y conserva paleografía y normalización por separado. Sus entradas son información léxica; no constituyen por sí mismas anotaciones visuales. La diversidad de fuentes requiere distinguir diccionario, variedad, época y tipo de evidencia. Sus [créditos](https://gdn.iib.unam.mx/creditos) identifican trabajos editoriales que no deben atribuirse al agente.

Ruta propuesta:

1. Mejorar la recuperación textual de las fichas ya admitidas, con fuente y campo original visibles.
2. Preparar relaciones explícitas entre entrada léxica y ficha pictográfica, manteniendo denominación, componente, valor contextual y lectura del conjunto separados.
3. Diseñar ejemplos visuales con identificador de imagen/recorte, documento, lámina, componentes, lectura propuesta, incertidumbre, evidencia y permisos de entrenamiento/evaluación. Un glifo relacionado con una palabra no se etiqueta automáticamente como equivalente a ella.
4. Evaluar un modelo visual ya existente antes de adaptarlo. [Qwen3-VL-4B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct) es un candidato con entrada de imágenes y texto; su ficha no demuestra competencia en náhuatl ni en estos documentos. Selección, memoria y latencia deben comprobarse en el equipo de destino.
5. Solo si hay datos aptos y una ventaja medible, preparar una adaptación multimodal nueva. El adaptador actual de Qwen3-0.6B es textual y no se convierte en un adaptador visual reutilizando sus pesos sobre otra arquitectura.

Actualmente `corpus/gdn-lexicon-v6.json` y el piloto pictográfico declaran `training: false`. La tarea autónoma respeta ese estado. No se encontró en las páginas consultadas una autorización suficiente para cambiarlo; la apertura de consulta no acredita permiso de entrenamiento. Revisar permisos por obra, edición, transcripción e imagen y dejar evidencia de la decisión. Se puede preparar infraestructura y propuestas sin introducir esos registros en los pesos.

## Alcance inicial del agente recurrente

Puede modificar código local, preparar contenido sustentado, mejorar la interfaz, aplicar lotes admitidos por el flujo editorial, ejecutar pruebas y dejar informes. Trabaja una prioridad por ejecución; no lanza escritores concurrentes sobre la misma carpeta. Mantiene los pesos publicados y el estado privado de Voces fuera de los cambios automáticos de contenido.

La primera fase no incluye servicios de pago, publicación externa ni descarga/entrenamiento de un modelo grande. La selección de modelo y el presupuesto de cómputo quedan explícitos antes de esa fase. Este límite permite empezar con extracción, recuperación y evaluación usando lo instalado. La evolución posterior debe incorporar un presupuesto medible, un directorio de experimento nuevo y una comparación reproducible.

## Primeras tareas

1. Implementar un informe de estado calculado y un registro persistente de tareas, con hashes y detección de resultados obsoletos.
2. Auditar conexiones y preparar el siguiente lote documental usando `pictography_pipeline`, sin cambiar los datos ya publicados.
3. Construir la batería de consultas con claves derivadas de fuente y etiquetas de revisión explícitas. Corregir el recuperador según errores reproducibles.
4. Preparar una nueva lectura con `lesson_builder`; preservar originales y ejercicios actuales.
5. Añadir al Laboratorio el estado de la ruta multimodal: datos disponibles, permisos pendientes, batería y resultados reales. Una ausencia de experimento debe mostrarse como tal.

No se inicia un entrenamiento real por crear esta guía. Las métricas históricas y sus hashes siguen describiendo los pesos existentes.
