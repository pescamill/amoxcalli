# Amoxcalli · identidad editorial

Primera aplicación, 7 de octubre de 2026. Dirección solicitada: libro de lectura de la SEP, sobriedad de publicaciones públicas mexicanas y referencias visuales nahuas, con una composición contemporánea propia.

## Una página de lectura

La interfaz toma del libro la portada, el índice, los márgenes, los capítulos numerados, las anotaciones y las fuentes al pie. La ilustración documental conduce a la lectura. El color distingue espacios y da ritmo; el texto se mantiene sobre fondos tranquilos.

Las referencias proporcionadas orientan la composición y la paleta. No se copian ilustraciones, portadas, escudos o firmas institucionales. La cenefa escalonada es una composición geométrica original, no una transcripción arqueológica ni un glifo con lectura. El interés visual en Teotihuacan no se presenta como evidencia de una equivalencia cultural o lingüística. Las imágenes con función educativa siguen siendo las fichas documentadas del catálogo y conservan su procedencia.

## Paleta y letra

| Uso | Color |
| --- | --- |
| Papel | `#f6f0e2` |
| Tinta de texto | `#302921` |
| Rojo de títulos, navegación y acciones | `#812d37` |
| Ocre de portada y anotaciones | `#c99538` |
| Azul de lectura y práctica | `#245b70` |
| Verde de apoyos y respuestas correctas | `#3d6252` |
| Texto secundario | `#685b4b` |

Títulos y pasajes: Palatino, Book Antiqua o Georgia, según el equipo. Controles y cuerpo: Avenir, Segoe UI o Arial. Son familias del sistema: no se descargan fuentes ni se añaden solicitudes a servicios tipográficos. La voz visual conserva tamaños legibles, espacio entre líneas, botones de al menos 44 px y foco visible. El color acompaña textos y estados; no es su único indicador.

Los fondos claros, el rojo y el ocre evocan papel, impresión e imágenes documentales. El azul y el verde introducen variación en ejercicios y apoyos. Evitar usar todos los acentos en un mismo bloque; evitar marcos decorativos que compitan con un pasaje.

## Voz escrita

Hablar como quien acompaña una lectura. Dar una acción concreta y dejar espacio para observar. No prometer fluidez, corrección o respaldo institucional que no se ha comprobado.

| Contexto | Criterio / ejemplo |
| --- | --- |
| Inicio | Invitar a leer: «Leamos palabra por palabra». Decir desde el principio que la ruta es clásica. |
| Lector | «Lee a tu ritmo. Toca una palabra para conocerla; muestra el español cuando lo necesites». |
| Cuaderno | Explicar qué guarda y dónde: palabras, pasajes y progreso en este navegador. |
| Voces | «Tu palabra, tu voz». Conservar denominación, escritura y decisiones de quien aporta. |
| Revisión | Indicar junto a la evidencia qué está comprobado y qué falta. No convertir cada invitación en una lista de advertencias. |
| Laboratorio | Nombrar método, resultado y límite con precisión. Una generación sigue siendo un borrador; el cambio de tono no mejora el modelo. |

No se inventan traducciones o lemas en náhuatl para nombrar botones. Los originales, las glosas heredadas y las explicaciones editoriales del corpus no se reescriben como parte de esta actualización de voz. Las notas que distinguen variantes, permisos y alcance glífico siguen visibles.

## Aplicación

`nahuatl_local/platform_web/amoxcalli.css` es la única hoja de estilos de la aplicación y de Voces en `/aportar`. Empieza con los tokens (`:root`: tinta, papel, arena, acento, tipografías) y sigue por secciones; la identidad editorial ya no es una capa que se superpone a otras hojas. El único `!important` es `[hidden]`. Voces carga su `style.css` propio y encima `amoxcalli.css`, que define alias (`--green`, `--lime`) para sus nombres de variables.

`edition-border.svg` contiene la cenefa original; `community_web/favicon.svg` usa un cuaderno abierto abstracto. Los iconos raster de instalación existentes se conservan. Las fichas de taller siguen imprimibles en negro y blanco, sin el marco de navegación.

Para una página nueva: reutilizar títulos, separadores, márgenes y controles antes de crear otra tarjeta o patrón, y tomar los colores de los tokens. La consolidación del 16 de octubre retiró las reglas anuladas y sin uso; la suite DOM y las capturas a 1280 y 375 px verifican los recorridos y la impresión.

## Estructura de la interfaz

Una sola caja de búsqueda en la cabecera (`#search`): en Diccionario, Fuentes y Fichas textuales filtra mientras se escribe; en las demás secciones abre Preguntar, que muestra el grupo de término (grafías, glifos, pasajes) con enlaces a Diccionario, Archivo y Consultar fichas. El Archivo y Consultar fichas conservan su formulario propio con filtros. Navegación principal: Lecturas, Diccionario, Glifos, Preguntar y Mis palabras; lo avanzado (Leer todos los pasajes, Archivo completo, Consultar fichas, Fichas textuales, Fuentes, Laboratorio, Proyecto, Voces, Opciones, exportar e instalar) está en «Más». Un solo aviso de revisión lingüística por página, bajo la cabecera.

Módulos del navegador (scripts clásicos que comparten funciones globales, en este orden): `app.js` (servido como `/corpus.js`: utilidades, estado, enrutador y búsqueda global), `terms.js`, `study.js` (cuaderno local), `words.js` (palabras, glifos y ayuda), `reading.js` (tarjeta de lectura y regreso al pasaje), `lessons.js`, `dictionary.js`, `notebook.js` (Mis palabras), `archive.js`, `library.js` (textos, fuentes, opciones), `contribute.js`, `documentary.js`, `morphology.js`, `evidence.js` (Preguntar), `pictography.js`, `project.js`, `laboratory.js`, `training-data.js`, `install.js`.
