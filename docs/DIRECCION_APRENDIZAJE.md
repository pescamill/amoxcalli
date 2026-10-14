# Dirección propuesta: aprender náhuatl mediante ejemplos

> Documento histórico de la decisión inicial. La dirección vigente del 7 de octubre de 2026 está en [PROPOSITO](PROPOSITO.md), con [propuesta de piloto](PILOTO_INSTITUCIONAL.md) y guía de colaboración en CONTRIBUTING. Las cifras siguientes describen el estado observado en septiembre.

Análisis del 29 de septiembre de 2026. Se revisaron código, informes, datos y la interfaz local. El usuario eligió **aprender náhuatl mediante ejemplos** como primer uso. Este documento propone el siguiente trabajo; no cambia la aplicación ni aprueba contenido lingüístico.

## Decisión de producto

Organizar Amoxcalli alrededor de una experiencia de lectura guiada y práctica breve. Una persona debe poder terminar una sesión y comprender mejor un ejemplo nuevo. El archivo bilingüe, las acepciones, las fuentes y las aportaciones alimentan ese recorrido.

La primera ruta requiere elegir entre lectura de náhuatl clásico y aprendizaje de una variedad contemporánea para comunicarse. Los textos históricos y las fichas existentes permiten preparar un piloto de lectura clásica. Una ruta contemporánea necesita una variedad/localidad concreta, ejemplos adecuados y colaboración de hablantes. Ambas pueden coexistir después como rutas identificadas; los ejercicios no deben mezclarlas silenciosamente.

## Lo que muestran los archivos actuales

| Parte | Evidencia | Consecuencia para el aprendizaje |
|---|---|---|
| Léxico | 12 acepciones y 14 formas; muchas notas de procedencia y pocas explicaciones de uso | Sirve como catálogo inicial, pero falta ayuda para comprender una frase y recordar sus palabras |
| Inventario nuevo | 100 grupos ordenados por frecuencia; empiezan yn, in, auh, ye, ca; también aparece de | La frecuencia aporta candidatos para el editor; no determina una secuencia didáctica ni identifica lemas |
| Corpus | 16.111 pares, variedades y obras mezcladas; sin consulta muestra los primeros registros del CSV | El principiante necesita elegir una tarea antes de enfrentarse a ese volumen |
| Prueba en navegador | Buscar flor devolvió 70 resultados; los primeros incluyen clásico y Sierra de Puebla | Falta explicar las formas, el contexto y la ruta lingüística del ejemplo |
| Textos anotados | Tres fichas: una con español y náhuatl, otra sin español, otra sin transcripción | La sección aún no ofrece un lector anotado suficiente para aprender |
| Fuentes | En los pasajes del archivo, el localizador es un registro CSV y el enlace lleva a la distribución del corpus | Abrir una fuente no sitúa necesariamente al alumno en una página de la obra |
| LLM | El informe HTTP de La casa y la flor registra una salida repetitiva; la generación con contexto también repite y se trunca | No hay evidencia suficiente para utilizar el generador como profesor o corrector |
| Colaboración | Propuestas, revisiones y versiones ya existen; la aprobación editorial ocurre por terminal | Hay una base útil para que especialistas preparen lecciones, pero falta una tarea editorial pedagógica |

Referencias locales: [interfaz](../nahuatl_local/platform_web/app.js), [archivo](../nahuatl_local/research.py), [inventario](../reports/lexicon-candidates.json), [prueba del modelo](../reports/webapp-model-smoke.json) y [gobernanza](LEXICO_GOBERNANZA.md).

El producto no tiene hoy un modelo explícito de lección, objetivos de aprendizaje, anotaciones de palabras, claves de ejercicio ni progreso didáctico. Los perfiles de Voces y sus puntos registran colaboración; no demuestran comprensión de la lengua. Las pruebas de software y chrF++ tampoco miden ese resultado.

## Recorrido recomendado

1. **Elegir una lección.** Título comprensible, objetivo concreto, duración aproximada y variedad/época visibles.
2. **Leer un ejemplo breve.** Náhuatl, traducción revisada y contexto suficiente. La traducción puede ocultarse para practicar.
3. **Consultar mientras se lee.** Pulsar una palabra abre una explicación breve del uso en ese ejemplo, grafías relevantes y más testimonios. Las notas morfológicas necesitan revisión; una traducción de oración no constituye alineación palabra por palabra.
4. **Practicar.** Reconocer el significado de una frase, completar una forma revisada o comparar dos ejemplos. La explicación del error debe ayudar a comprender la respuesta.
5. **Reconocer algo nuevo.** Mostrar un ejemplo distinto del practicado para comprobar transferencia. Después, guardar palabras para repaso.

Las citas completas, anotaciones de edición y estados de cotejo quedan disponibles en un panel de fuente. El alumno ve primero el objetivo, el texto y la ayuda; el editor conserva la trazabilidad completa.

## Primer piloto: alcance pequeño y terminado

Propuesta de alcance: **tres lecciones, doce ejemplos revisados y unas veinte formas explicadas**. Son objetivos de entrega, no materiales que ya estén validados. Conviene completar este recorrido antes de ampliar la colección a cientos de entradas.

| Entrega | Trabajo | Comprobación |
|---|---|---|
| Material del piloto | Elegir ruta; seleccionar doce ejemplos cortos de una o dos fuentes; cotejar traducciones, grafías, contexto y permisos | Cada ejemplo tiene fuente, localizador y responsable; su variedad está identificada |
| Léxico contextual | Escribir las explicaciones de las formas que aparecen en esos ejemplos, con análisis pertinente al nivel | La ayuda explica el ejemplo seleccionado; no ofrece equivalencias universales |
| Lector | Vista bilingüe, ayuda al pulsar palabras, mostrar/ocultar español y panel de fuente | Un principiante puede leer sin navegar entre tres catálogos |
| Ejercicios | Dos tipos de ejercicios con claves revisadas y retroalimentación específica | Cada respuesta aceptada y explicación está justificada por el material |
| Prueba con personas | Probar con cinco principiantes y una persona competente en la ruta elegida | Observar navegación, errores y comprensión de un ejemplo nuevo |

Una primera prueba de producto podría exigir que cuatro de cinco personas completen una lección sin ayuda del desarrollador y que al menos tres comprendan un ejemplo nuevo comparable, según una rúbrica preparada por el revisor. Estos son criterios propuestos para decidir el siguiente lote; una muestra tan pequeña no demuestra eficacia educativa general.

## Interfaz

La navegación principal propuesta es **Aprender · Leer · Mis palabras · Aportar**. La consulta completa del archivo y el laboratorio del LLM pueden permanecer en herramientas avanzadas. La portada muestra una lección para comenzar y el progreso de quien regresa.

En la búsqueda general se deben distinguir coincidencias en náhuatl y en español, resaltar la expresión encontrada y permitir palabra exacta, frase y grafías documentadas. Agrupar por obra y variedad ayuda a comparar testimonios. Para lectura continuada se necesita reconstruir y verificar el orden de la edición: los IDs contiguos del CSV no prueban proximidad en la obra original.

El glifo puede aportar una sección cultural de un ejemplo cuando tenga contexto y documentación. No sustituye la explicación lingüística ni se presenta como escritura automática de una oración.

## Función del léxico

Convertirlo en el glosario del lector y del repaso. Priorizar las formas que necesitan las primeras lecciones, con significado contextual, ejemplos y relaciones ortográficas revisadas. Las entradas pueden ampliarse hacia un diccionario después, manteniendo sentidos y variantes separados.

El Gran Diccionario Náhuatl permite consultar palabra exacta, inicio o cualquier parte, distinguiendo náhuatl, grafía normalizada y traducción. Puede servir como referencia de consulta enlazada y de procedencia; su interfaz no autoriza copiar automáticamente todos sus contenidos. [GDN, UNAM](https://gdn.iib.unam.mx/).

## Función del corpus

Usarlo como banco de testimonios y herramienta editorial. Cada ejemplo didáctico debe tener una selección y anotación deliberadas. El archivo completo puede seguir disponible para exploración.

La auditoría de variantes aporta información necesaria para escoger fuentes, pero aprobar 1.687 etiquetas no convierte esas filas en lecciones. Tampoco la longitud de una oración determina su dificultad: fechas, nombres propios, arcaísmos, referencias culturales y construcciones complejas pueden aparecer en textos breves.

## Función del LLM

Conservar los pesos y el laboratorio, y suspender nuevas corridas de entrenamiento como prioridad de producto. La nueva experiencia puede funcionar con ejemplos, claves y explicaciones revisadas.

Una función futura evaluable sería ayudar al editor a preparar borradores en español o proponer candidatos de ejercicios, siempre sobre material identificado. Hay que probar esa tarea específicamente antes de incorporarla; la capacidad actual del modelo no se infiere de que sea un LLM. La segmentación morfológica y la corrección de respuestas libres tampoco pueden darse por resueltas.

Si el desarrollo del traductor local sigue siendo un objetivo de investigación, mantenerlo como línea separada con pares de referencia y revisión lingüística. La métrica relevante para la experiencia principal es lo que comprende y recuerda el alumno.

## Colaboración y presentación institucional

Tras verificar el piloto, abrir tareas pequeñas: cotejar un ejemplo, mejorar una explicación, proponer un ejercicio y, para una variedad contemporánea, aportar audio con consentimiento y revisión. Cada lección muestra versión y responsable. La cola de aprobación web se vuelve prioritaria cuando participen varios editores; las cuentas y roles se diseñan a partir de ese trabajo real.

La propuesta a una institución puede ser concreta: revisar doce ejemplos y tres lecciones, identificar responsables y probarlas con principiantes. La revisión docente y lingüística aporta más al piloto que una petición genérica de respaldar todo el proyecto.

Como referencia de diseño, ENALLT distingue cursos generales y talleres de comprensión de lectura. Su material Inic ome nahuatlahtolamoxtli combina situaciones cotidianas, práctica oral y escrita, juegos de vocabulario, proyectos y audio. Estos recursos sugieren patrones para una ruta pedagógica; no se incorporan al proyecto mediante este análisis. [Oferta ENALLT](https://enallt.unam.mx/lenguas/cursos-lenguas-ciudad-universitaria/nahuatl/oferta-cursos-talleres), [material didáctico](https://publicaciones.enallt.unam.mx/index.php?op=book&page=catalog&path%5B%5D=85&press=Publicaciones_ENALLT).

## Orden de trabajo

1. Elegir ruta lingüística y un objetivo de la primera lección.
2. Revisar una lección completa con cuatro ejemplos y sus ayudas.
3. Construir el lector y un ejercicio que permitan recorrerla de principio a fin.
4. Probar con principiantes y corregir lo observado.
5. Completar el piloto de tres lecciones.
6. Añadir repaso, cola editorial y nuevas lecciones conforme exista material revisado.

Las siguientes ampliaciones generales —más corpus, más entradas sin uso definido, reconocimiento glífico automático o cambio de modelo— se decidirán por las necesidades observadas en ese piloto.


## Primera implementación

El usuario aprobó avanzar y precisó que las imágenes deben ser glifos asociados a palabras de las fuentes existentes. La primera versión implementada incluye tres lecturas con doce fragmentos, lector, ejercicios, diccionario de 24 acepciones con 21 imágenes documentales y cuaderno de repaso. El estado editorial continúa siendo borrador: la revisión lingüística y la prueba con principiantes siguen pendientes. Detalles y comprobaciones: [entrega del piloto](../reports/APRENDIZAJE_GLIFOS_2026-09-29.md).


## Laboratorio y seguimiento

El laboratorio quedó visible en la navegación principal, con explicación del modelo, resultados históricos y sus límites. Es una línea de experimentación; las lecturas y ejercicios continúan funcionando con material editorial. La actualización de interfaz no entrenó nuevos pesos. [Estado interno y siguientes pasos](PROGRESO_INTERNO.md), [laboratorio](LABORATORIO.md).
