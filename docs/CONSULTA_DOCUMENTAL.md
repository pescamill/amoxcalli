# Consulta documental local · v1

`#consultar` permite buscar una palabra, una frase breve o un ID de ficha, pasaje o aparición. Devuelve originales, normalización catalogada, acepciones, fuentes y enlaces. Comparar grafías significa mostrar ambos campos y su igualdad literal; no elegir un significado ni interpretar un glifo. Se consulta texto del catálogo; no se procesan ni copian imágenes.

El índice `nahuatl_local.documentary_retrieval` usa solamente stdlib y los registros públicos actuales de `CorpusStore`, todos los 16.111 pasajes del archivo y todas las tablas del catálogo pictográfico. No importa el recuperador SFT, la batería ni sus referencias. La API `GET /api/documentary?query=...` vuelve a comprobar las fichas públicas en cada petición; si cambia una publicación o se retira un registro, reconstruye el índice. No conserva una versión retirada como resultado.

## Método fijado antes de medir

Configuración `documentary-lookup-v1`: hasta 1.000 caracteres y 20 resultados; identificador literal completo: 1.000 puntos; etiqueta completa por tokens (grafía, lema y aliases explícitos de su acepción): 100 más longitud; coincidencia de al menos dos tokens útiles (uno si la consulta tiene uno), ponderada por frecuencia inversa. Orden estable: puntuación descendente, tipo e ID. La comparación auxiliar quita acentos y distingue límites de palabras; nunca altera originales. Las palabras funcionales españolas se excluyen dentro de frases extensas, pero pueden consultarse solas. No se extraen argumentos mediante plantillas de preguntas. El mismo método atiende consultas breves y preguntas que contienen IDs o grafías.

Las formas recuperadas llevan su acepción vinculada; las acepciones distintas permanecen separadas. La consulta muestra un aviso cuando hay más de 20 coincidencias y cuando no encuentra evidencia. Una coincidencia relacionada no acredita una respuesta completa. IDs explícitos y preguntas sobre campos son una prueba de consulta documental, no de comprensión general del lenguaje.

## Medición y reproducción

```sh
.venv/bin/python -m nahuatl_local.documentary_retrieval_evaluation
.venv/bin/python -m nahuatl_local.documentary_retrieval_evaluation --check
```

El evaluador accede exclusivamente a desarrollo mediante `load_development(modality='textual')`; el índice solo recibe pregunta y fuentes públicas. La reserva se conserva intacta y solo participa en validación estructural y fingerprint de la batería. Se mide cada uno de los 123 casos. `correct_source` exige todos los IDs y campos de la referencia, con valores originales. Compartir Molina/GDN no basta. `supported_citations` comprueba cada campo devuelto, hash de fila/archivo y URL documentada. Cobertura, abstención y coincidencias relevantes se reportan por separado.

El informe registra tiempos reales de construcción, consultas y total con `perf_counter`, además de memoria Python con `tracemalloc` (no memoria total del proceso). Repetir una medición cambia tiempos; verificar y repetir el diagnóstico contra el mismo informe conserva los bytes. El validador reproduce respuestas con el método vigente y vuelve a cotejar referencias; una lista de booleanos o texto generado no completa el hito técnico.

Los campos editados públicamente en esta instalación se identifican como `public_records`, distintos de la transcripción distribuida; no se certifican como evidencia literal de una fila congelada. Las fuentes mantienen condiciones originales. La consulta local no habilita entrenamiento, evaluación con imágenes, copia de imágenes ni envío externo. Cotejo primario, juicio lingüístico y ensayo con personas siguen pendientes.

## Registro de desarrollo del ciclo 006

Primera corrida: 119/123 casos completos, 121 con coincidencias, 2 abstenciones; 840/860 campos requeridos. Se conservan las exclusiones de A y Y dentro de preguntas extensas. Una comprobación independiente con «agua» mostró que las formas no heredaban las etiquetas españolas explícitas de su acepción vinculada. Se añadieron esas etiquetas y aliases al índice de su forma para permitir la consulta bilingüe con original y fuente juntos; no se infieren sinónimos. Esta modificación se registra antes de la corrida final y no responde a claves de reserva. También se separó validez de citas devueltas de cobertura de todas las URLs solicitadas: una respuesta parcial puede tener citas válidas y seguir incompleta. La corrida inicial se conserva en el respaldo del informe.

La verificación final en navegador detectó que la política CSP bloqueaba el estilo inline de los originales en PRE, causando desbordamiento horizontal. La regla `.card.documentary-hit pre` vive ahora en `/corpus.css`, con `white-space:pre-wrap` y corte de cadenas largas; la presentación no requiere excepciones CSP. El stylesheet entra en hashes del informe y del diagnóstico. La prueba DOM comprueba estilo calculado y ausencia de inline, y el coordinador verifica anchura real en navegador.

## Dependencias separadas · ciclo 014

`documentary_retrieval_evaluation.IMPLEMENTATION` y `documentary_evaluation.FIXED`, junto con los hashes de `PublicSources`, determinan la vigencia de la medición: ranking/citas, store/variantes, corpus completo, configuración de fuentes, batería, receta de referencias y evaluador. `EVALUACION_DOCUMENTAL.md` permanece como especificación de la receta fija; no es una guía de cadencia de trabajo. Un cambio en esas entradas requiere revalidar y, si la medición queda obsoleta, medir una corrida nueva con respaldo.

UI, navegación, CSS, API de presentación, diagnóstico y guías de proceso no son entradas del ranking. Sus cambios no exigen remedir las 123 consultas. `documentary_laboratory.DISPLAY_SOURCES` mantiene los hashes de pantalla/QA en `presentation_hashes` de la evidencia DOM/HTTP; `iteration.source_manifest()` continúa detectando UI y guías. La migración 014 cambia el contrato del evaluador y mide una única corrida nueva: se conserva la anterior y se comparan todas las respuestas/auditorías, sin atribuirle una mejora del ranking.
