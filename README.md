# amoxcalli · Amoxcalli

[English](docs/README.en.md)

**Aprender a leer náhuatl clásico mediante ejemplos con fuente: comprender un fragmento, contrastarlo y volver al documento.**

Amoxcalli reúne lecturas breves, un diccionario, referencias glíficas y un archivo bilingüe en una aplicación local. Empieza con náhuatl clásico; el archivo conserva las etiquetas de otras variantes sin tratarlas como intercambiables. La intención es dar contexto a las palabras: dónde aparecen, cómo se escribieron, qué podemos afirmar y qué sigue sin resolverse.

Este repositorio, `amoxcalli`, conserva el proyecto en desarrollo. Ya se puede leer, buscar, practicar y aportar. Todavía faltan revisión lingüística, cotejo de fuentes primarias y pruebas con estudiantes. El laboratorio permite inspeccionar nuestros experimentos con modelos y sus fallos; las traducciones generadas todavía son malas.

La prioridad es una lectura que una persona pueda comprender y comprobar. Para enseñar una variedad actual hace falta una ruta acordada con sus hablantes, materiales propios y revisión de esa variedad. El proyecto conserva un espacio para esa colaboración; todavía no ofrece ese curso. [Propósito y prioridades](docs/PROPOSITO.md).

## Para empezar

Con Python 3.11 o posterior, desde la carpeta del proyecto:

```bash
bash scripts/plataforma.sh
```

Abre [http://127.0.0.1:8766](http://127.0.0.1:8766). Lecturas, diccionario, archivo y Voces funcionan con la biblioteca estándar de Python. El modelo tiene dependencias adicionales; puedes explorar la aplicación antes de instalarlas.

Una pequeña expedición: abre **Flores y cantos**, oculta el español y pulsa una forma que reconozcas. Guarda la palabra, encuentra otro ejemplo en el archivo y vuelve al ejercicio. O empieza por **Aves**: un ave en un poema y las aves de un relato pueden llevarte a preguntas distintas. Es parte de la gracia.

La presentación toma la forma de un cuaderno de lectura: portada ocre, tinta roja, capítulos y anotaciones junto a los pasajes. Los glifos proceden de las fuentes; la cenefa es una composición propia. La [guía de identidad y voz](docs/IDENTIDAD_EDITORIAL.md) conserva los criterios para nuevas páginas.

## Qué puedes hacer

| Espacio | Uso actual |
| --- | --- |
| **Aprender** | Recorrer doce lecturas con ayuda contextual, traducción ocultable y ejercicios basados en la grafía del pasaje. Hay 28 preguntas de comprensión con claves citadas de la traducción original. |
| **Leer** | Explorar los 48 fragmentos seleccionados, sus notas y procedencia. Consultar una palabra en Diccionario o Archivo y volver al mismo pasaje, también por teclado. |
| **Analizar cualquier palabra** | Pulsar cualquier palabra de una lectura para ver su segmentación (*ni-qu-itta*), la entrada del diccionario, otros pasajes con la misma raíz y pistas del corpus paralelo con sus pasajes de apoyo. Mostrar una glosa interlineal del fragmento. Análisis por reglas, diccionario y corpus, sin LLM. [Guía](docs/MORFOLOGIA.md). |
| **Preguntar** | Escribir una palabra en cualquier grafía (*kuali*, *nocal*) o en español (*¿cómo se dice mujer?*) y recibir el análisis, las entradas y pasajes del archivo con la misma raíz, cada uno con su motivo. Une ortografía moderna y colonial; se abstiene sin evidencia. Sin LLM. [Guía y medición](docs/EVIDENCIA.md). |
| **Ficha para taller** | Desde Leer, preparar una lectura textual para imprimir o guardar como PDF, con traducciones y claves opcionales. Descargar el JSON con claves, fuentes, versiones y hashes para revisión. |
| **Diccionario** | Consultar palabras, acepciones, formas históricas y conexiones visuales documentadas. La primera página conserva 24 entradas representativas; las demás siguen el orden alfabético náhuatl. Las búsquedas priorizan la coincidencia exacta y ofrecen continuar en el archivo cuando falta una entrada. |
| **Mis palabras** | Crear un cuaderno propio y repasar con intervalos. Guarda también el fragmento de origen para volver a él durante el repaso. El progreso se guarda en ese navegador, sin cuenta. |
| **Archivo y herramientas** | Buscar en español o náhuatl, filtrar por variante, obra y época, consultar fuentes y preparar exportaciones con notas de derechos. |
| **Consultar fichas** | Buscar palabras, frases breves o IDs en el diccionario, el archivo y el catálogo pictográfico; contrastar originales, acepciones y fuentes, y volver al Diccionario para estudiar una palabra. |
| **Laboratorio** | Ver la recuperación documental medida y los modelos aún sin ejecutar en esa batería; inspeccionar fallos, costes y fuentes. Probar búsqueda, reglas o generación experimental, consultar los pares usados por el adaptador y sus resultados históricos. |
| **Aportar · Voces** | Proponer texto, voz, traducciones, formas y conexiones; indicar variante y permisos, revisar o retirar aportaciones. |
| **Proyecto y colaboración** | Entender propósito, públicos y pendientes; descargar las guías de colaboración y del piloto institucional. |

Sirve para estudio personal, exploración de textos, preparación de actividades de lectura y trabajo editorial. También permite estudiar cómo se construye un conjunto de datos y cómo cambia un modelo al entrenarlo. La utilidad en clase y la calidad pedagógica aún necesitan pruebas con personas.

Para docentes y colectivos, la primera colaboración propuesta es revisar una lectura de cuatro pasajes y probarla en un taller acompañado. Para hablantes actuales, primero se acuerdan comunidad, variedad, objetivos, coautoría, reconocimiento o remuneración y permisos. Para una institución, se ofrece un piloto acotado con evidencias y responsables por confirmar. No se declara aval gubernamental ni certificación. [Propuesta de piloto](docs/PILOTO_INSTITUCIONAL.md).

La aplicación puede instalarse desde el navegador. En un teléfono, instalación y micrófono requieren HTTPS. El servidor debe seguir encendido; la pantalla de desconexión no guarda aportaciones pendientes. Consulta la [guía de instalación y acceso móvil](docs/WEBAPP.md).

## Dónde estamos

Inventario actualizado el **8 de octubre de 2026**, conservando los lotes anteriores:

| Área | Estado |
| --- | --- |
| Lecturas | **12 recorridos, 48 pasajes de 10 obras**. Las nuevas selecciones trabajan casas, animales, piedra y leña, árboles y cerros, fuego y viento, y Sol y Luna en relatos. |
| Diccionario | **575 entradas/acepciones**: 26 curadas y 549 transcripciones automáticas de Molina vía GDN; 578 formas. |
| Referencias visuales | **140 registros**; 139 entradas tienen una imagen de fuente y 436 esperan evidencia visual. Se utilizan 24 URLs de imágenes documentales. |
| Índice pictográfico | **311 apariciones** (297 glifos y 14 personajes), 142 denominaciones y 613 componentes contextualizados, en 13 láminas de 3 conjuntos. Es un índice documental separado de las acepciones didácticas. |
| Archivo bilingüe | **16.111 pares de Axolotl**, con 33 obras identificadas y etiquetas originales de variante. |
| Entrenamiento histórico visible | **650 pares efectivamente recorridos** por el adaptador, con español, náhuatl e identificación de fuente. |
| Preparación actual para modelos | **5.462 pares clásicos**, separados por obra: 2.161 entrenamiento, 2.049 validación y 1.252 prueba. Los pesos existentes corresponden a una preparación anterior. |
| Revisión de las lecturas | [Auditoría de 62 tareas](reports/learning-audit-lecturas-003-2026-10-07/inventory.md). El cotejo primario, la revisión especializada y las pruebas con principiantes siguen pendientes. |

Una referencia guardada no siempre es un glifo de toda la palabra. La interfaz distingue glifo simple, elemento de compuesto, iconografía y apoyo relacionado o contextual. Una imagen de agua junto a un pasaje ayuda a observarlo; por sí sola no demuestra cómo se escribió la oración. Las transcripciones históricas tampoco son automáticamente una definición moderna ni un análisis morfológico.

El [lote de seis nuevas lecturas](reports/LECTURAS_003_2026-10-07.md) conserva íntegramente las seis anteriores y sus claves. Los [informes de septiembre](reports/LECTURAS_002_2026-09-30.md) y del [recorrido conectado](reports/RECORRIDO_CONECTADO_2026-10-07.md) conservan las comprobaciones históricas. Las pruebas de software verifican comportamiento técnico, no corrección filológica ni eficacia educativa.

## Palabras y escritura pictográfica

Amoxcalli conserva el diccionario para aprender y añade **Glifos**: un índice documental con denominaciones, apariciones, componentes y valores registrados por Tlachia. El índice reúne 13 láminas de tres conjuntos, 297 glifos, 14 personajes y 142 denominaciones distintas. El recorrido **Aprender a observar** compara `calli` en tres documentos; una ficha permite volver al diccionario y guardar la palabra cuando hay un vínculo explícito. Las lecturas del catálogo se atribuyen a sus autores y siguen pendientes de cotejo primario propio.

La [guía del diccionario pictográfico](docs/DICCIONARIO_PICTOGRAFICO.md) explica entidades, límites y la importación por lotes con caché, hashes y preservación de fichas. Se procesan páginas estructuradas con scripts, sin un LLM. Las 575 acepciones y las lecturas existentes se conservan al ampliar. El nombre anterior, Scriptorium, permanece en algunas claves técnicas para no perder progreso.

La [ampliación del 8 de octubre](reports/PICTOGRAFIA_LOTES_004_2026-10-08.md) añadió 220 apariciones en cuatro lotes con respaldos, sin modificar las fichas anteriores ni crear equivalencias nuevas. La meta técnica de 300 apariciones está cubierta. Siguen pendientes la revisión especializada y las pruebas de comprensión con personas.

La [batería documental](docs/EVALUACION_DOCUMENTAL.md) prepara 123 consultas textuales y 51 observaciones de fichas para desarrollo, con 37 y 15 casos en reserva aparte. Sus claves conservan campos originales, fuentes y hashes; las familias de entradas, obras e imágenes se separan antes del reparto. Las observaciones visuales contienen enlaces y campos del catálogo; el uso de imágenes en un modelo sigue pendiente.

La [consulta documental](docs/CONSULTA_DOCUMENTAL.md), disponible desde Diccionario, Archivo y Laboratorio, recupera fichas con campos originales y citas comprobables. La medición sobre las **123 consultas textuales de desarrollo** obtuvo **119 completas**, dos parciales y dos abstenciones; recuperó 840 de 860 campos requeridos. Son preguntas con grafías o IDs de fichas conocidas: el resultado no demuestra comprensión general ni calidad de traducción. La reserva sigue sin evaluar. [Método, fallos y pruebas](reports/RECUPERACION_006_2026-10-08.md).

El [Laboratorio](docs/LABORATORIO.md) presenta esa medición junto al modelo textual y un candidato multimodal. Ambos figuran **sin ejecutar sobre esta batería**, con puntuación y coste sin medir. Los experimentos históricos permanecen aparte; todavía no hay una comparación de rendimiento entre métodos. Se pueden reproducir los cuatro fallos y descargar resúmenes públicos sin claves esperadas ni casos reservados. [Informe de la presentación y sus comprobaciones](reports/LABORATORIO_007_2026-10-08.md).

El visor de preparación visual permite recorrer **51 casos documentales de desarrollo**, con pregunta, enlaces de fuente y referencias ocultas inicialmente. No procesa imágenes ni ejecuta un modelo. Comprueba las dependencias instaladas y señala que falta la arquitectura requerida. [Informe y pruebas](reports/PREPARACION_VISUAL_016_2026-10-12.md); [propuesta de primera prueba local con imágenes](docs/PRUEBA_VISUAL_LOCAL.md), pendiente de autorización.

Los resúmenes del Laboratorio reutilizan una caché en memoria y comprueban los hashes de sus fuentes antes de cada acceso. En una muestra local, cinco descargas posteriores promediaron **9,34 ms**, frente a **2,12 s** antes; la primera carga aún tarda unos dos segundos. Los resultados documentales se conservan. [Medición y pruebas](reports/CACHE_LABORATORIO_008_2026-10-08.md).

Las consultas que parten de una lectura conservan el pasaje de origen al recorrer Diccionario, Archivo y cotejo de fichas. Los enlaces llevan el texto actual de búsqueda, incluso si se edita sin enviar el formulario. El retorno enfoca ese fragmento sin marcar respuestas ni cambiar el progreso. Se comprobó con teclado y a 360/390 px de ancho; falta probarlo en teléfonos físicos. [Comprobaciones y límites](reports/CONTINUIDAD_COTEJO_012_2026-10-09.md).

Aves está **disponible para estudiar**: cuatro pasajes, ocho ejercicios y una comparación final entre el ave del poema y las aves del relato. [Abrir Aves en la instalación local](http://127.0.0.1:8766/#aprender/aves). Las ayudas siguen pendientes de revisión lingüística y prueba con lectores. El [expediente Aves 012](reports/reading-review/aves-012/package.md) conserva el material y las tareas humanas como una instantánea histórica; no se vuelve a preparar por cambios de interfaz. Su vigencia global anterior no se presenta como actual. [Entrega y corrección de metodología](reports/METODOLOGIA_Y_AVES_014_2026-10-12.md).

En «¿Hay otra palabra que quieras entender?», **Comparar aquí** muestra hasta dos fragmentos con la misma escritura, su español ocultable y sus fuentes, conservando la lectura abierta. La búsqueda completa en el Archivo sigue disponible. [Entrega y comprobaciones](reports/APRENDER_COMPARANDO_015_2026-10-12.md).

El [último diagnóstico integral](reports/iterations/iteration-014/inventory.md) distingue preparación técnica de revisión humana; conserva el estado anterior a esta mejora de interfaz. Las tareas humanas pendientes no significan que todas las lecturas estén bloqueadas. La prioridad es cerrar recorridos útiles y corregir dificultades observadas; el cotejo especializado, las pruebas con principiantes y los usos nuevos de modelos e imágenes mantienen sus requisitos propios.

## Analizar palabras: morfología y concordancia por raíz

El náhuatl es polisintético: *nocal*, *calco* y *calli* comparten la raíz *cal*, pero una búsqueda por palabra completa no los relaciona, y la grafía colonial multiplica las variantes (*yhuan/ihuan/iuan*). Un analizador transparente propone segmentaciones en la grafía de la fuente, las enlaza con el diccionario y declara su base (diccionario, partícula, corpus o solo reglas). Sobre 52 formas de referencia, 77 % de segmentaciones exactas (92 % entre las tres primeras), frente a 15 % solo con reglas. La raíz de 42 % de las palabras del corpus clásico queda enlazada al diccionario, frente a 20 % por coincidencia exacta; la búsqueda por raíz recupera 6.391 pasajes frente a 3.493. Las cifras, la línea base y los límites están en el [informe](reports/MORFOLOGIA_EVALUACION.md); el diseño, en [ARCHITECTURE.md](docs/ARCHITECTURE.md) (inglés), y el plan por iteraciones, en [ROADMAP.md](docs/ROADMAP.md). Las tablas y el conjunto de referencia esperan revisión especializada.

## Crecer por lotes

Un [script de candidatos léxicos](docs/CANDIDATOS_CONEXIONES_LEXICAS.md) compara denominaciones pictográficas y formas del diccionario sin un LLM. El [primer lote de ocho pares](reports/lexical-link-review/candidatos-013/candidates.md) conserva acepciones, fuentes y componentes contextuales para cotejarlos juntos. La coincidencia de escritura no demuestra equivalencia de sentido: todos siguen pendientes y los nueve vínculos publicados se conservan. Preparar de nuevo verifica los archivos y protege las notas existentes. [Implementación, pruebas y límites](reports/CONEXIONES_CANDIDATAS_013_2026-10-12.md).

El [pipeline editorial](docs/EDITORIAL_PIPELINE.md) reúne candidatos de fuentes cacheadas, prepara hasta 50 entradas y 100 concordancias, comprueba transcripciones y dependencias, separa excepciones y produce una propuesta revisable. La incorporación es aditiva, con respaldo y comprobaciones para conservar lo existente. La extracción y el enlace utilizan scripts, sin llamadas a un LLM.

Las lecturas se construyen con [recetas explícitas](docs/LECTURAS_PIPELINE.md): IDs de pasajes, palabras seleccionadas, notas y distractores conocidos. El ensamblador verifica hashes de fuente, conexiones y respuestas tomadas del texto. La selección y el juicio lingüístico siguen siendo trabajo editorial.

```bash
python3 -m nahuatl_local.lesson_audit
python3 -m nahuatl_local.editorial_release --help
python3 -m nahuatl_local.lesson_builder --help
```

El lote `batch-007-v9` está incorporado. `batch-009-v11` quedó preparado y verificado, sin publicar; la ampliación de comprensión del 7 de octubre cambió el hash de las lecturas. Para continuar hay que preparar un lote con ID nuevo y la caché local de fuentes. El lote anterior `batch-008-v10` quedó desactualizado tras ampliar las lecturas.

Lo que más puede hacer crecer el proyecto ahora es añadir buenos contextos y corregir malas conexiones: ampliar las lecturas con criterios repetibles, resolver ambigüedades con evidencia primaria, completar referencias visuales donde exista documentación y probar si una persona aprende con los ejercicios. La [cola de trabajo](docs/LEARNING_ITERATION_PLAN.md) y el [registro de progreso](docs/PROGRESO_INTERNO.md) conservan esas decisiones.

El siguiente paso prioritario es revisar una lectura completa y probar su comprensión antes de otra ampliación general. Una imagen pendiente se conserva como tal: no se inventa una conexión para completar una cuota. El modelo se evaluará después sobre casos reservados y revisados.

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

Puedes empezar por una duda concreta, sin programar: ID del pasaje, problema, fuente/localizador, propuesta y alcance. [Cómo contribuir](CONTRIBUTING.md) explica revisión, cambios por lotes y comprobaciones. Las plantillas del repositorio permiten registrar correcciones de contenido o dificultades de uso. Cada aportación mantiene sus permisos; la licencia del código y la visibilidad del repositorio son decisiones distintas.

Para actualizar una instalación, respalda y conserva `data/community/`. El cuaderno y el progreso de lectura viven en el almacenamiento del navegador. Guías de [Voces](docs/VOCES.md), [arquitectura](docs/PLATAFORMA.md) y [gobernanza del léxico](docs/LEXICO_GOBERNANZA.md).

## Código, fuentes y comprobaciones

Python, SQLite y HTML/CSS/JavaScript; sin una API de inferencia externa. El modelo opcional utiliza PyTorch, Transformers y PEFT. El repositorio separa `corpus/` (contenido), `editorial/` (decisiones y propuestas), `nahuatl_local/` (aplicación y scripts), `docs/` (guías), `reports/` (evidencia técnica) y `tests/` (comprobaciones).

```bash
python3 -m unittest discover -s tests
```

Para las comprobaciones de interfaz (Node.js, solo desarrollo):

```bash
npm ci --ignore-scripts
npm run test:ui
npm run test:offline
```

Algunas comprobaciones de entrenamiento y cotejo editorial requieren dependencias, datos preparados o páginas cacheadas que no forman parte de una instalación mínima. Sus requisitos aparecen en las guías correspondientes.

El código y la documentación originales tienen licencia [MIT](LICENSE). Qwen utiliza Apache-2.0; la distribución Elotl declara MPL-2.0. Los permisos de cada obra, edición y traducción requieren revisión independiente. Los textos, imágenes y adaptadores derivados conservan sus propias condiciones; no quedan relicenciados como MIT.

Las imágenes se enlazan desde las fuentes, con atribución y condiciones en cada ficha. No se añaden imágenes generadas. Consulta [fuentes](docs/FUENTES.md) y [avisos de terceros](THIRD_PARTY_NOTICES.md) antes de reutilizar o redistribuir contenido.
