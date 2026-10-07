# amoxcalli · Scriptorium

[English](docs/README.en.md)

**Aprender náhuatl leyendo: encontrar una palabra, reconocerla en otro pasaje y volver a su fuente.**

Scriptorium reúne lecturas breves, un diccionario, referencias glíficas y un archivo bilingüe en una aplicación local. Empieza con náhuatl clásico; el archivo conserva las etiquetas de otras variantes sin tratarlas como intercambiables. La intención es dar contexto a las palabras: dónde aparecen, cómo se escribieron, qué podemos afirmar y qué sigue sin resolverse.

Este repositorio, `amoxcalli`, conserva el proyecto en desarrollo. Ya se puede leer, buscar, practicar y aportar. Todavía faltan revisión lingüística, cotejo de fuentes primarias y pruebas con estudiantes. El laboratorio permite inspeccionar nuestros experimentos con modelos y sus fallos; las traducciones generadas todavía son malas.

## Para empezar

Con Python 3.11 o posterior, desde la carpeta del proyecto:

```bash
bash scripts/plataforma.sh
```

Abre [http://127.0.0.1:8766](http://127.0.0.1:8766). Lecturas, diccionario, archivo y Voces funcionan con la biblioteca estándar de Python. El modelo tiene dependencias adicionales; puedes explorar la aplicación antes de instalarlas.

Una pequeña expedición: abre **Flores y cantos**, oculta el español y pulsa una forma que reconozcas. Guarda la palabra, encuentra otro ejemplo en el archivo y vuelve al ejercicio. O empieza por **Aves**: un ave en un poema y las aves de un relato pueden llevarte a preguntas distintas. Es parte de la gracia.

## Qué puedes hacer

| Espacio | Uso actual |
| --- | --- |
| **Aprender** | Recorrer seis lecturas con ayuda contextual, traducción ocultable y ejercicios basados en la grafía del pasaje. |
| **Leer** | Explorar los 24 fragmentos seleccionados, sus notas y procedencia. |
| **Diccionario** | Consultar palabras, acepciones, formas históricas y conexiones visuales documentadas. La primera página conserva 24 entradas representativas; las demás siguen el orden alfabético náhuatl. |
| **Mis palabras** | Crear un cuaderno propio y repasar con intervalos. El progreso se guarda en ese navegador, sin cuenta. |
| **Archivo y herramientas** | Buscar en español o náhuatl, filtrar por variante, obra y época, consultar fuentes y preparar exportaciones con notas de derechos. |
| **Laboratorio** | Comparar búsqueda de ejemplos, reglas léxicas limitadas y generación experimental; ver los pares español/náhuatl utilizados por el adaptador y los informes de entrenamiento. |
| **Aportar · Voces** | Proponer texto, voz, traducciones, formas y conexiones; indicar variante y permisos, revisar o retirar aportaciones. |

Sirve para estudio personal, exploración de textos, preparación de actividades de lectura y trabajo editorial. También permite estudiar cómo se construye un conjunto de datos y cómo cambia un modelo al entrenarlo. La utilidad en clase y la calidad pedagógica aún necesitan pruebas con personas.

La aplicación puede instalarse desde el navegador. En un teléfono, instalación y micrófono requieren HTTPS. El servidor debe seguir encendido; la pantalla de desconexión no guarda aportaciones pendientes. Consulta la [guía de instalación y acceso móvil](docs/WEBAPP.md).

## Dónde estamos

Inventario del contenido incorporado el **30 de septiembre de 2026**:

| Área | Estado |
| --- | --- |
| Lecturas | **6 recorridos, 24 pasajes de 6 obras**: flor; Sol y Luna; tierra, casa y cerro; agua y tierra; flores y cantos; aves. |
| Diccionario | **575 entradas/acepciones**: 26 curadas y 549 transcripciones automáticas de Molina vía GDN; 578 formas. |
| Referencias visuales | **140 registros**; 139 entradas tienen una imagen de fuente y 436 esperan evidencia visual. Se utilizan 24 URLs de imágenes documentales. |
| Archivo bilingüe | **16.111 pares de Axolotl**, con 33 obras identificadas y etiquetas originales de variante. |
| Entrenamiento histórico visible | **650 pares efectivamente recorridos** por el adaptador, con español, náhuatl e identificación de fuente. |
| Preparación actual para modelos | **5.462 pares clásicos**, separados por obra: 2.161 entrenamiento, 2.049 validación y 1.252 prueba. Los pesos existentes corresponden a una preparación anterior. |
| Revisión de las lecturas | Cola de 36 tareas: 1 resuelta editorialmente, 4 bloqueadas y 31 abiertas. El cotejo primario de los sentidos trabajados sigue pendiente. |

Una referencia guardada no siempre es un glifo de toda la palabra. La interfaz distingue glifo simple, elemento de compuesto, iconografía y apoyo relacionado o contextual. Una imagen de agua junto a un pasaje ayuda a observarlo; por sí sola no demuestra cómo se escribió la oración. Las transcripciones históricas tampoco son automáticamente una definición moderna ni un análisis morfológico.

Los [informes de la última expansión](reports/LECTURAS_002_2026-09-30.md) registran lo añadido y lo conservado. La comprobación local anterior a esta publicación ejecutó 179 pruebas, con un fallo esperado de una función ortográfica desactivada; el informe de interfaz contiene seis bloques de comprobaciones aprobadas. Esto verifica comportamiento técnico, no corrección filológica.

## Crecer por lotes

El [pipeline editorial](docs/EDITORIAL_PIPELINE.md) reúne candidatos de fuentes cacheadas, prepara hasta 50 entradas y 100 concordancias, comprueba transcripciones y dependencias, separa excepciones y produce una propuesta revisable. La incorporación es aditiva, con respaldo y comprobaciones para conservar lo existente. La extracción y el enlace utilizan scripts, sin llamadas a un LLM.

Las lecturas se construyen con [recetas explícitas](docs/LECTURAS_PIPELINE.md): IDs de pasajes, palabras seleccionadas, notas y distractores conocidos. El ensamblador verifica hashes de fuente, conexiones y respuestas tomadas del texto. La selección y el juicio lingüístico siguen siendo trabajo editorial.

```bash
python3 -m nahuatl_local.lesson_audit
python3 -m nahuatl_local.editorial_release --help
python3 -m nahuatl_local.lesson_builder --help
```

El lote `batch-007-v9` está incorporado. `batch-009-v11` quedó preparado y verificado, pendiente de publicación; sus páginas de consulta deben estar disponibles en la caché local para reproducir el cotejo. El lote anterior `batch-008-v10` quedó desactualizado tras ampliar las lecturas.

Lo que más puede hacer crecer el proyecto ahora es añadir buenos contextos y corregir malas conexiones: ampliar las lecturas con criterios repetibles, resolver ambigüedades con evidencia primaria, completar referencias visuales donde exista documentación y probar si una persona aprende con los ejercicios. La [cola de trabajo](docs/LEARNING_ITERATION_PLAN.md) y el [registro de progreso](docs/PROGRESO_INTERNO.md) conservan esas decisiones.

## El laboratorio y el LLM

El modelo es **Qwen3-0.6B adaptado con LoRA**, con 1.146.880 parámetros entrenables. Hubo un piloto de 400 pasos, una continuación fallida y una continuación corregida de 250 pasos adicionales. No se preentrenó una base desde cero. El generador puede repetir palabras, inventar formas o cambiar el sentido.

El laboratorio hace visibles los pares de entrenamiento, las pérdidas, ejemplos de salida y métricas históricas. Una reducción de pérdida o un chrF++ mayor en una muestra pequeña no demuestra fidelidad. Las métricas de preparaciones y muestras distintas se presentan por separado. Añadir lecturas, editar el diccionario o guardar propuestas **no entrena el modelo**.

Para experimentar con el modelo local, utiliza Python 3.11/3.12 y:

```bash
bash scripts/iniciar.sh --enable-model
```

La primera ejecución instala dependencias y descarga la base fijada (~1,5 GB). Los adaptadores `best` de los experimentos se conservan en el repositorio; la base y los estados del optimizador quedan fuera. La aplicación principal funciona sin ellos. Los informes permiten inspeccionar lo ocurrido sin cargar pesos.

Un próximo experimento útil sería comparar recuperación, base y adaptador sobre las mismas frases reservadas, después de revisar las alineaciones. El potencial está en construir evidencia para saber qué ayuda al lector. Consulta la [ficha del modelo](MODEL_CARD.md), su [estado](docs/ESTADO_MODELO.md), el [laboratorio](docs/LABORATORIO.md) y la [guía para mejorarlo](docs/MEJORAR.md). Para entrenamiento por etapas: [AUTOTRAIN](docs/AUTOTRAIN.md). Este checkout no incluye el estado necesario para reanudar exactamente las ejecuciones históricas.

## Aportar y cuidar el trabajo

Voces admite texto y audio, variantes o autodenominaciones y permisos independientes de publicación y entrenamiento. Las propuestas manuales o por CSV del laboratorio quedan pendientes de revisión. Los perfiles, audios, aportaciones, bases SQLite y respaldos locales se excluyen de Git.

Para actualizar una instalación, respalda y conserva `data/community/`. El cuaderno y el progreso de lectura viven en el almacenamiento del navegador. Guías de [Voces](docs/VOCES.md), [arquitectura](docs/PLATAFORMA.md) y [gobernanza del léxico](docs/LEXICO_GOBERNANZA.md).

## Código, fuentes y comprobaciones

Python, SQLite y HTML/CSS/JavaScript; sin una API de inferencia externa. El modelo opcional utiliza PyTorch, Transformers y PEFT. El repositorio separa `corpus/` (contenido), `editorial/` (decisiones y propuestas), `nahuatl_local/` (aplicación y scripts), `docs/` (guías), `reports/` (evidencia técnica) y `tests/` (comprobaciones).

```bash
python3 -m unittest discover -s tests
```

Algunas comprobaciones de entrenamiento y cotejo editorial requieren dependencias, datos preparados o páginas cacheadas que no forman parte de una instalación mínima. Sus requisitos aparecen en las guías correspondientes.

El código y la documentación originales tienen licencia [MIT](LICENSE). Qwen utiliza Apache-2.0; la distribución Elotl declara MPL-2.0. Los permisos de cada obra, edición y traducción requieren revisión independiente. Los textos, imágenes y adaptadores derivados conservan sus propias condiciones; no quedan relicenciados como MIT.

Las imágenes se enlazan desde las fuentes, con atribución y condiciones en cada ficha. No se añaden imágenes generadas. Consulta [fuentes](docs/FUENTES.md) y [avisos de terceros](THIRD_PARTY_NOTICES.md) antes de reutilizar o redistribuir contenido.
