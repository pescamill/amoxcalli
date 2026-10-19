# Amoxcalli

[English](docs/README.en.md)

**Aprender a leer náhuatl clásico mediante ejemplos con fuente: comprender un fragmento, contrastarlo y volver al documento.**

Amoxcalli reúne lecturas guiadas, unidades de gramática, un analizador de palabras, un buscador de grafías (clásica, moderna y de cada variedad), un diccionario con fuentes, glifos documentados, fichas de dioses y del calendario, y un archivo bilingüe de 16.111 pasajes. Cada resultado dice de dónde viene: una entrada del diccionario, un pasaje del archivo, una ficha pictográfica o una regla. **Sin evidencia, la aplicación se abstiene.** Todo funciona sin LLM y con la biblioteca estándar de Python.

**Estado (17 de octubre de 2026).** Se puede leer, practicar, analizar palabras, buscar en cualquier grafía, consultar dioses y calendario, y aportar. Lo automático (ayudas, entradas de Wiktionary, unidades y lecturas nuevas) está marcado como tal y **pendiente de revisión lingüística**. Faltan el cotejo con fuentes primarias y la prueba con principiantes: son las colaboraciones que buscamos ([propuesta de piloto](docs/PILOTO_INSTITUCIONAL.md), [propósito](docs/PROPOSITO.md)). El plan vigente es [docs/ROADMAP.md](docs/ROADMAP.md).

## Probarlo

Con Python 3.11 o posterior y git:

```bash
git clone https://github.com/pescamill/amoxcalli.git
cd amoxcalli
make demo
```

Abre <http://127.0.0.1:8766>. La primera vez, `make demo` prepara los análisis derivados (alrededor de un minuto) y arranca el servidor; mientras tanto la aplicación muestra «Preparando el análisis…». Después arranca en segundos. Un solo proceso sirve la aplicación, Voces (`/aportar`) y la API:

```bash
bash scripts/amoxcalli.sh serve [opciones]   # detiene un servidor previo en el mismo puerto
```

| Opción | Efecto |
| --- | --- |
| `--host`, `--port` | Interfaz y puerto (por omisión `127.0.0.1:8766`). Para el teléfono en la misma red: [docs/WEBAPP.md](docs/WEBAPP.md). |
| `--demo` | Demostración pública de solo lectura: se puede consultar todo, pero no se guardan perfiles, aportaciones ni grabaciones. |
| `--public-origin https://dominio` | Detrás de un proxy HTTPS: acepta ese Host y lo exige como Origin de escritura. |
| `--db ruta` | Base local de perfiles, aportaciones y propuestas (por omisión `data/community/voces.sqlite3`). Va antes de `serve`. |
| `--explain-model claude` | Explicaciones redactadas por Claude en Preguntar; envía la pregunta y los pasajes citados a la API de Anthropic. Sin esta opción, nada sale del equipo. |

En Windows o sin `make`: `py -m nahuatl_local.platform serve` con las mismas opciones.

Con Docker (imagen de unos 230 MB, en modo demostración):

```bash
docker build -t amoxcalli .
docker run -p 7860:7860 amoxcalli
```

**Publicarlo** paso a paso (Google Cloud Run, gratis con poco tráfico; Hugging Face Spaces con PRO; una máquina virtual): [docs/DESPLIEGUE.md](docs/DESPLIEGUE.md). Con todos los índices construidos usa unos 760 MB de RAM: hace falta un plan de al menos 1 GB.

**Un recorrido de cinco minutos:** abre **Lecturas → Reconocer una flor**, pulsa *NIQUITTA* (*ni-qu-itta*, «yo-lo-veo») y muestra la glosa interlineal. Escribe *kuali* en la búsqueda: aparece *cualli* con sus grafías por variedad y sus fuentes. Pregunta *¿cómo se dice mujer?* en **Preguntar** y pulsa las citas de la explicación. Abre **Más → Dioses y calendario** y busca *Huitzilopoxtli*.

## Qué hay

| Espacio | Qué hace |
| --- | --- |
| **Lecturas** | 12 lecturas guiadas (48 pasajes reales de 10 obras): traducción ocultable, ejercicios sobre la grafía del pasaje, 28 preguntas de comprensión citadas de la traducción original. Toda palabra se puede analizar y hay glosa interlineal, también durante los ejercicios (solo se oculta la palabra que falta). Ficha imprimible para taller. |
| **Unidades de gramática** (en «Más») | 4 unidades cortas de gramática (absolutivo, posesivos, locativos, sujeto y objeto) con ejercicios de emparejar, identificar morfemas, armar palabras y traducir pasajes breves; repaso espaciado con ejemplos. Son borradores automáticos con respuestas respaldadas por el pasaje y el análisis. [ROADMAP 5a](docs/ROADMAP.md). |
| **Analizar una palabra** | Segmentación en la grafía de la fuente, entrada del diccionario, pasajes con la misma raíz y pistas del corpus paralelo, cada una con su base (diccionario, corpus, reglas o nombre propio). [Guía](docs/MORFOLOGIA.md). |
| **Buscar en cualquier grafía** | Se escribe como uno escribe (*kuali*, *kualli*, *qualli*, *cuali*, o con un error) y aparecen al instante las posibilidades con sus fuentes, aunque esa grafía exacta no esté en el archivo. Perfiles colonial, ACK y SEP/INALI, y rasgos por variedad. **Relaciona; no impone un estándar.** [Guía](docs/GRAFIAS.md). |
| **Preguntar** | Una palabra en cualquier grafía, una pregunta en español (*¿cómo se dice mujer?*) o el ID de una ficha: análisis, entradas y pasajes con su motivo, una explicación breve donde cada frase cita su evidencia, y las fichas con sus originales. Se abstiene sin evidencia. [Guía](docs/EVIDENCIA.md) · [fichas](docs/CONSULTA_DOCUMENTAL.md). |
| **Diccionario y Glifos** | 3.790 acepciones: 26 curadas, 549 transcripciones automáticas de Molina vía GDN y 3.215 lemas de Wiktionary (CC BY-SA, extracción automática). 480 apariciones pictográficas de 21 láminas de Tlachia. Cada término reúne sus grafías, pasajes por variedad y glifos con su alcance (palabra completa, componente o relación). Notas de gramática de Carochi (1645). [Guía](docs/DICCIONARIO_PICTOGRAFICO.md) · [fuentes](docs/FUENTES.md). |
| **Dioses y calendario** (en «Más») | 26 deidades, figuras, epítetos y lugares, cada dato con su fuente; el tonalpohualli (20 signos con su glifo del Telleriano-Remensis, 13 numerales, 20 trecenas) y las 18 veintenas. Las grafías de los nombres llevan a la misma ficha. Cuatro lecturas de mitología y una unidad del calendario esperan revisión. [Guía](docs/DIOSES_CALENDARIO.md). |
| **Archivo completo** (en «Más») | 16.111 pares de Axolotl (unos 6.000 de náhuatl clásico y 10.000 de variedades actuales) con sus etiquetas de variante y obra; una sola búsqueda para palabras, grafías y frases. |
| **Mis palabras** | Cuaderno y repaso espaciado en el navegador, sin cuenta; guarda el pasaje de origen. |
| **Aportar · Voces** | Proponer texto, voz, formas y conexiones con permisos separados de publicación y entrenamiento; todo queda pendiente de revisión y se puede retirar. [Guía](docs/VOCES.md). |
| **Laboratorio (histórico)** (en «Más») | Qué se probó con un traductor experimental (Qwen3-0.6B + LoRA), sus cifras y por qué se retiró. El código está archivado en [experiments/llm/](experiments/llm/README.md); la aplicación no carga dependencias de aprendizaje automático. |

## Cifras y de dónde salen

Una sola evaluación produce todas: `make eval` regenera [reports/EVALUACION.md](reports/EVALUACION.md) y `make check` vuelve a medir y falla si una cifra cambió sin regenerarla. `dev` se usa para ajustar; `test` solo para medir.

| Medición | Resultado (test) |
| --- | --- |
| Segmentación morfológica, prueba ciega v2 (91 formas escritas antes de medir) | 78 % exacta (palabras 67 %, partículas 94 %, nombres propios 100 %); 89 % en el conjunto v1 |
| Palabras del corpus clásico con raíz enlazada al diccionario | 60,4 % (28,0 % por coincidencia exacta; era 41,8 % antes de Wiktionary) |
| Buscador de grafías (`spelling-search-v1`) | Palabra buscada en primer lugar 94,2 %, entre las tres primeras 97,1 %; ninguna asociación errónea |
| Índice de términos (`term-groups-v1`) | Consulta → grupo correcto 90,5 %; glifos con su alcance 100 % |
| Preguntar (32 consultas) | Entrada correcta en primer lugar 92,3 %, frente a 42 % de la búsqueda exacta; siempre con un pasaje pertinente |
| Fichas de Preguntar (123 consultas documentales) | 780 de 790 campos exactos |
| Traductor LoRA, histórico (chrF++) | 22,4 con contexto, frente a 27,2 de devolver el pasaje más cercano: **no es un traductor**; retirado |

Son comprobaciones técnicas sobre conjuntos pequeños escritos por el equipo; no sustituyen la revisión de una persona experta ni demuestran que alguien aprenda.

## Colaborar

Buscamos personas que revisen lecturas y entradas, docentes que prueben una lectura en un taller acompañado, hablantes de variedades actuales que quieran ver su forma de escribir reconocida, e instituciones que permitan usar sus fuentes. Con hablantes, primero se acuerdan comunidad, variedad, objetivos, reconocimiento y permisos. Una duda concreta también ayuda: ID del pasaje, problema, fuente y propuesta. [Cómo contribuir](CONTRIBUTING.md).

## Desarrollo

```bash
npm ci --ignore-scripts   # jsdom, solo para las pruebas de interfaz
make test                 # pruebas de Python y de interfaz
make eval                 # regenera la tabla de evaluación
make check                # vuelve a medir y comprueba que las cifras publicadas siguen vigentes
```

La CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) corre `make check` y `make test` sobre un clon limpio. Un cambio solo de interfaz se verifica con las pruebas de interfaz y no mueve ninguna cifra; un cambio en datos, analizador, índices o conjuntos de evaluación sí (`make eval`).

| Carpeta | Contenido |
| --- | --- |
| `corpus/` | Contenido distribuido: archivo Axolotl, lecturas, catálogo léxico, glifos, entidades, lotes editoriales |
| `editorial/` | Decisiones y propuestas editoriales (lecturas y unidades en revisión) |
| `evaluation/`, `configs/` | Conjuntos de evaluación congelados y configuraciones |
| `nahuatl_local/` | Servidor, análisis y scripts (Python stdlib); `platform_web/` es la interfaz |
| `reports/` | Solo informes vigentes y regenerables ([índice](reports/README.md)) |
| `docs/` | Guías: [ROADMAP](docs/ROADMAP.md) (plan), [ARCHITECTURE](docs/ARCHITECTURE.md) (diseño), [DESPLIEGUE](docs/DESPLIEGUE.md) (publicar), [HISTORIA](docs/HISTORIA.md) (lo hecho), [PLATAFORMA](docs/PLATAFORMA.md) (operar una instalación) |
| `experiments/llm/` | Laboratorio del LLM, archivado |

## Licencias y fuentes

Código y documentación originales: [MIT](LICENSE). Los textos, imágenes y datos de terceros conservan sus condiciones y no quedan relicenciados como MIT: el corpus Axolotl (distribución Elotl, MPL-2.0), las entradas de Wiktionary (CC BY-SA 4.0, con atribución en cada ficha), el Vocabulario de Molina vía el Gran Diccionario Náhuatl (UNAM) y el catálogo Tlachia (UNAM; las imágenes se cargan desde su sitio, con atribución). No hay imágenes generadas. El Gran Diccionario Náhuatl ampliado y el Códice Florentino esperan permiso ([borradores de cartas](docs/permisos/)). Ver [fuentes](docs/FUENTES.md) y [avisos de terceros](THIRD_PARTY_NOTICES.md).
