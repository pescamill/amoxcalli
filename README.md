# Amoxcalli

[English](docs/README.en.md)

**Aprender a leer náhuatl clásico mediante ejemplos con fuente: comprender un fragmento, contrastarlo y volver al documento.**

Amoxcalli es una aplicación local que reúne lecturas breves, un diccionario con fuentes, un índice de glifos y un archivo bilingüe de 16.111 pasajes. Cada respuesta remite a su evidencia: una entrada del diccionario, un pasaje del archivo o una ficha documental. El análisis de palabras y la consulta funcionan **sin LLM**; el modelo experimental vive aparte, en el Laboratorio.

**Estado (15 de octubre de 2026).** Se puede leer, buscar, analizar palabras, practicar y aportar. Faltan la **revisión lingüística** de ayudas y ejercicios, el **cotejo con fuentes primarias** y la **prueba con principiantes**: son las colaboraciones que buscamos ([propuesta de piloto](docs/PILOTO_INSTITUCIONAL.md), [propósito](docs/PROPOSITO.md)). El plan vigente es [docs/ROADMAP.md](docs/ROADMAP.md).

## Probarlo

Con Python 3.11 o posterior (solo biblioteca estándar):

```bash
make demo
```

Abre <http://127.0.0.1:8766>. `make demo` prepara una vez los análisis derivados (~1 min) y arranca el servidor. Un solo proceso sirve la aplicación, Voces (`/aportar`) y la API; el arranque es siempre el mismo script:

```bash
bash scripts/amoxcalli.sh serve [opciones]   # solo biblioteca estándar; detiene un servidor previo en el puerto
bash scripts/amoxcalli.sh setup [opciones]   # además prepara .venv, dependencias y pesos del modelo local
```

| Opción | Efecto |
| --- | --- |
| `--host`, `--port` | Interfaz y puerto (por omisión `127.0.0.1:8766`). Para el teléfono en la misma red, la IP del equipo: [docs/WEBAPP.md](docs/WEBAPP.md). |
| `--public-origin https://dominio` | Detrás de un proxy HTTPS: acepta ese Host y lo exige como Origin de escritura. |
| `--db ruta` | Base local de perfiles, aportaciones y propuestas (por omisión `data/community/voces.sqlite3`). |
| `--disable-model` | No ofrece generación aunque el modelo esté instalado (se ofrece solo cuando base, adaptador y dependencias existen). `--adapter` elige otro adaptador. |
| `--explain-model claude` | Explicaciones redactadas por Claude en Preguntar; envía la pregunta y los pasajes citados a la API de Anthropic. Sin ella, nada sale del equipo. |

En Windows: `py -m nahuatl_local.platform serve` con las mismas opciones (`--db` va antes de `serve`).

Un recorrido corto: abre **Aprender → Flores y cantos**, oculta el español y pulsa una palabra para ver su análisis (*ni-qu-itta*), su entrada y otros pasajes con la misma raíz. Después escribe *kuali* o *¿cómo se dice mujer?* en **Preguntar**.

## Qué hay

| Espacio | Qué hace |
| --- | --- |
| **Aprender** | 12 lecturas guiadas (48 pasajes de 10 obras) con traducción ocultable, ejercicios sobre la grafía del pasaje y 28 preguntas de comprensión con claves citadas de la traducción original. |
| **Leer** | Los mismos fragmentos con procedencia. Toda palabra se puede analizar; glosa interlineal del fragmento. Ficha imprimible para taller. |
| **Analizar una palabra** | Segmentación en la grafía de la fuente, entrada del diccionario, pasajes con la misma raíz y pistas del corpus paralelo, cada una con su base (diccionario, corpus o reglas). [Guía](docs/MORFOLOGIA.md). |
| **Preguntar** | Una palabra en cualquier grafía (*kuali*, *nocal*) o una pregunta en español: análisis, entradas y pasajes con su motivo, y una explicación breve donde cada frase cita su evidencia. Se abstiene sin evidencia. [Guía](docs/EVIDENCIA.md). |
| **Diccionario y Glifos** | 575 acepciones y 578 formas (26 curadas, 549 transcripciones automáticas de Molina vía GDN); 311 apariciones pictográficas de Tlachia en 13 láminas. Una imagen junto a una entrada no siempre escribe la palabra: la ficha dice qué relación documenta. [Guía](docs/DICCIONARIO_PICTOGRAFICO.md). |
| **Archivo y Consultar fichas** | 16.111 pares de Axolotl con sus etiquetas de variante y obra; consulta de fichas con campos originales y citas comprobables. [Guía](docs/CONSULTA_DOCUMENTAL.md). |
| **Mis palabras** | Cuaderno y repaso espaciado en el navegador, sin cuenta; guarda el pasaje de origen. |
| **Laboratorio** | Mediciones, pares de entrenamiento y el modelo experimental Qwen3-0.6B + LoRA, con sus fallos. [Guía](docs/LABORATORIO.md) · [ficha del modelo](MODEL_CARD.md). |
| **Aportar · Voces** | Proponer texto, voz, formas y conexiones con permisos separados de publicación y entrenamiento; todo queda pendiente de revisión. [Guía](docs/VOCES.md). |

## Cifras y de dónde salen

Cada cifra sale de un comando; `make reports` los regenera y `make check` comprueba que siguen vigentes ([reports/README.md](reports/README.md)).

| Medición | Resultado | Informe |
| --- | --- | --- |
| Segmentación morfológica (52 formas de referencia) | 77 % exacta; 41,8 % de las palabras del corpus clásico con raíz enlazada al diccionario (20,3 % por coincidencia exacta) | [MORFOLOGIA_EVALUACION.md](reports/MORFOLOGIA_EVALUACION.md) |
| Preguntar (32 consultas de prueba) | Entrada correcta en primer lugar 92 % frente a 42 % de la búsqueda exacta; grafías modernas 0 % → 100 % | [EVIDENCIA_EVALUACION.md](reports/EVIDENCIA_EVALUACION.md) |
| Consulta documental (123 consultas de desarrollo) | 119 completas, 2 parciales, 2 abstenciones; 840/860 campos exactos | `reports/documentary-retrieval-v1.json` |
| Modelo LoRA (20 frases de prueba, chrF++) | 22,4 con contexto recuperado, frente a 27,2 de devolver el pasaje más cercano: **no es un traductor** | [MODEL_CARD.md](MODEL_CARD.md) |

Son comprobaciones técnicas sobre conjuntos pequeños escritos por el equipo; no sustituyen la revisión de una persona experta ni demuestran que alguien aprenda.

## Colaborar

Para docentes y colectivos, la primera colaboración propuesta es revisar una lectura de cuatro pasajes y probarla en un taller acompañado. Para hablantes de variedades actuales, primero se acuerdan comunidad, variedad, objetivos, reconocimiento y permisos; el proyecto todavía no ofrece ese curso. Una duda concreta también ayuda: ID del pasaje, problema, fuente y propuesta. [Cómo contribuir](CONTRIBUTING.md).

## Desarrollo

```bash
npm ci --ignore-scripts
make test
```

`make test` corre la suite Python y la suite DOM (jsdom). CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) hace lo mismo sobre un clon limpio, más `make check`. Un cambio solo de interfaz se verifica con la suite DOM y **no** exige regenerar informes; un cambio en ranking, datos, batería o evaluador sí (`make reports`). El laboratorio LLM necesita además `requirements.txt` (PyTorch, Transformers, PEFT) y Python 3.11/3.12; sus pruebas se omiten si faltan.

| Carpeta | Contenido |
| --- | --- |
| `corpus/` | Contenido distribuido: archivo Axolotl, lecturas, catálogo, glifos, lotes editoriales publicados |
| `editorial/` | Decisiones y propuestas editoriales |
| `evaluation/`, `configs/` | Conjuntos de referencia y la batería documental |
| `nahuatl_local/` | Servidor, análisis y scripts (Python stdlib); `platform_web/` es la interfaz |
| `reports/` | Solo informes vigentes y regenerables ([índice](reports/README.md)) |
| `docs/` | Guías: [ROADMAP](docs/ROADMAP.md) (plan), [HISTORIA](docs/HISTORIA.md) (lo hecho hasta hoy), [ARCHITECTURE](docs/ARCHITECTURE.md) (diseño), [PLATAFORMA](docs/PLATAFORMA.md) (operar una instalación) |

## Licencias y fuentes

Código y documentación originales: [MIT](LICENSE). Qwen: Apache-2.0; la distribución Elotl declara MPL-2.0. Los textos, imágenes y adaptadores derivados conservan sus propias condiciones y no quedan relicenciados como MIT. Las imágenes se enlazan desde sus fuentes con atribución; no hay imágenes generadas. Ver [fuentes](docs/FUENTES.md) y [avisos de terceros](THIRD_PARTY_NOTICES.md).
