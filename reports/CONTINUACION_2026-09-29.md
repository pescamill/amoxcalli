# Continuación de Scriptorium — 29 de septiembre de 2026

Se retomó el estado descrito en el adjunto y se verificaron los archivos actuales. Las fases de preparación y evaluación ya tenían código, pero faltaban diagnósticos correctos, una referencia nueva de recuperación y la conexión de BM25 con la búsqueda principal.

## Glifos

El `<img>` estaba presente, pero el encabezado CSP heredado solo permitía imágenes locales. Scriptorium permite ahora exclusivamente el dominio `https://aztecglyphs.wired-humanities.org` en `img-src`; las otras directivas se conservan. No se copiaron imágenes ni se cambiaron los permisos de los registros. Se reinició el servidor local y se verificó la carga desde el navegador:

| Ficha | Tamaño natural de la imagen |
|---|---|
| agua / atl | 190 × 186 |
| casa / calli | 437 × 332 |
| flor / xochitl | 98 × 92 |
| árbol florido / xochicuahuitl | 480 × 475 |

Las cuatro imágenes aparecen con atribución y enlace a su ficha. El servidor continúa en `http://127.0.0.1:8766`. El script de arranque interpreta `--port N` y `--port=N`, y su búsqueda de procesos se limita a quienes escuchan en ese puerto, sin incluir clientes conectados.

## Preparación y diagnóstico

El conjunto actual mantiene **5.462 pares**, divididos en **2.161/2.049/1.252** por obra. Al regenerarlo con el tokenizador local, los tres archivos JSONL resultaron idénticos byte a byte. Solo se actualizaron manifiestos y estadísticas. La normalización de almacenamiento conserva el CSV original como transcripción exacta; la limpieza de espacios y controles no es reversible por sí misma.

El tokenizador Qwen es ByteLevel BPE con `byte_fallback=false`. El 15,30% anterior contaba tokens de un carácter, incluidos caracteres ASCII normales; no medía fallos de cobertura. La auditoría corregida registra cero tokens desconocidos y cero fallos de ida y vuelta, con resultado `ok`. [Diagnóstico completo](tokenizer-audit.json).

Las longitudes por texto, sin instrucción ni respuesta concatenada, tienen medias de 51,534 tokens españoles y 62,782 náhuatl; p95 de 121 y 149. Ocho textos españoles y 78 náhuatl superan 192 tokens. Esto no equivale al número de pares que caben en el formato de entrenamiento. [Preparación actual](corpus-preparation.json) y [manifest histórico de los pesos existentes](corpus-preparation-legacy.json).

## Recuperación y evaluación

La búsqueda `/api/research` y el contexto del laboratorio usan ahora un mismo índice BM25 perezoso sobre los 16.111 registros originales. Las consultas náhuatl usan reglas seguras de comparación, con ç/tz y v/u; h, qu/cu e y/in siguen fuera del conjunto aprobado. Los resultados conservan transcripciones y procedencia. Los filtros por ISO, obra, época y la paginación se conservan; la navegación sin consulta mantiene el orden del archivo.

El benchmark mantiene un índice separado sobre `train.jsonl`. Se añadió `--retrieval-only` y se ejecutó en 100 ejemplos de validación, sin cargar ni ejecutar el modelo. Se recuperó exclusivamente de las 2.161 filas de entrenamiento; se detectó un solapamiento y quedan 99 ejemplos sin señal de solapamiento.

| Métrica | Todos (100) | Sin señal de solapamiento (99) |
|---|---:|---:|
| chrF++ de recuperación | 16,0123 | 16,0790 |
| IC 95% por ejemplo | 14,6975–17,3760 | 14,7545–17,4202 |
| IC 95% por obra | 12,7430–19,1416 | 12,8501–19,1416 |

Los intervalos usan 1.000 remuestreos y solo dos obras. La muestra, los datos y la recuperación difieren del informe antiguo de 20 ejemplos de prueba; sus cifras no son directamente comparables. No se ha vuelto a medir al generador ni entrenado nuevos pesos. [Informe completo](benchmark-retrieval-validation-current-full.json), [resumen](benchmark-retrieval-validation-current.json) y [hoja humana](benchmark-retrieval-validation-current.review.csv).

## Variantes y ampliación editorial

La auditoría identifica ocho grupos y 2.157 filas sin variante/ISO. Propone **1.687 `nci`**: Diario (1.483), Sexta Relación (160) y La llave del náhuatl (44). Diario es un texto colonial de Chimalpahin en edición moderna. Las **470 filas restantes** necesitan decisiones más específicas: Revista mezcla trabajos, Milpa Alta plantea una discrepancia taxonómica y la autoría moderna de Historia de México no identifica por sí sola su registro lingüístico.

El [informe de variantes](variant-audit-2026-09-29/README.md) enlaza la evidencia bibliográfica; `audit.json` conserva cada huella y `review.csv` las decisiones pendientes. El comando de aplicación exige aprobación y responsable y produce una copia derivada con manifiesto, sin sobrescribir el original ni los splits. La validación rechaza IDs incongruentes y obras con etiquetas existentes incompatibles.

El inventario de [candidatos léxicos](lexicon-candidates.json) y su [hoja de curación](lexicon-candidates.csv) permiten ampliar las 12 acepciones mediante testimonios, sin convertir tokens en definiciones inventadas. El catálogo editorial no se amplía automáticamente. El [plan de ampliación y gobernanza](../docs/LEXICO_GOBERNANZA.md) describe cotejo, sentidos, permisos y las entregas necesarias para revisión abierta con varios responsables.

Pendientes de decisión: aprobación de las etiquetas propuestas, método de ampliación editorial y uso educativo/comercial para seleccionar futuras fuentes externas. La clasificación y la consulta bibliográfica no habilitan entrenamiento de esas fuentes.

## Validación

La suite completa ejecutó **129 pruebas** en 4,451 segundos, con resultado `OK` y un fallo esperado existente que documenta la regla agresiva de eliminación de h todavía desactivada. Incluye pruebas HTTP reales en puertos temporales de localhost, aislamiento de entrenamiento, diagnóstico del tokenizador, clasificación revisada y extracción de concordancias. [Salida de pruebas](tests-2026-09-29.txt).

También se comprobó el encabezado CSP y la carga real de los cuatro glifos en el navegador. `bash -n scripts/plataforma.sh` pasó. La huella del CSV original sigue siendo `ed8e85f560e78c43385f91ac99d08dee071183749bc1f1aa1b88f1b3a2530878`.
