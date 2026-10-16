# Historia de Amoxcalli · 16 de septiembre – 15 de octubre de 2026

Resumen único de los registros de ciclo que se retiraron del árbol el 15 de octubre de 2026 (`docs/PROGRESO_INTERNO.md`, `docs/ITERACIONES.md`, `docs/TRABAJO_AUTONOMO.md`, unos 460 archivos de `reports/` y las guías de herramientas eliminadas). Todo sigue en el historial de git: `git log -- docs/PROGRESO_INTERNO.md` o `git show 86c217f:reports/<archivo>`. Las cifras vigentes están en el [README](../README.md) y en [reports/](../reports/README.md); las de abajo son las de cada fecha.

## Qué se aprendió del proceso

- **Una entrega por ciclo se volvió un paquete por ciclo.** Del 7 al 14 de octubre, cada mejora de interfaz producía informe fechado, registro de pruebas, diagnóstico, cola de tareas, repetición byte a byte y verificación del coordinador. Hubo ciclos con más de 30 archivos para un cambio visible pequeño.
- **Las compuertas de hash mezclaban medición y presentación.** El Laboratorio exigía una «evidencia de pantalla» con hashes de `platform.py`, `app.js`, `style.css`, etc.; cualquier cambio de interfaz invalidaba la comparación y obligaba a regenerarla (16 fallos en la primera corrida en macOS, 14 oct). Desde el 15 de octubre la presentación se verifica con la suite DOM y las compuertas cubren solo entradas medidas.
- **Las mediciones sí resistieron.** La recuperación documental se re-midió seis veces (ciclos 006, 007, 011, 012, 014 y tras el manejador 500 del 14 oct) solo por cambios de hashes y las 123 respuestas, campos y auditorías fueron idénticas salvo tiempos; las métricas no cambiaron nunca.
- **Lo pendiente no depende de software.** Revisión lingüística, cotejo primario y prueba con principiantes estaban pendientes desde septiembre y siguen pendientes.

## Cronología

**16–23 sep · Corpus y modelo.** Fuentes y decisiones de uso ([FUENTES.md](FUENTES.md)). Axolotl (16.111 pares) vía Comunidad Elotl; preparación clásica separada por obra. Qwen3-0.6B + LoRA, 400 pasos en CPU: NLL de validación 5,40 → 3,79. En 20 frases de prueba, chrF++ 15,4 (base), 16,0 (adaptador), 22,4 (adaptador + RAG) frente a 27,2 de devolver el pasaje más cercano: el generador no es un traductor ([MODEL_CARD.md](../MODEL_CARD.md)).

**27–29 sep · Una plataforma.** Voces (texto y voz con permisos) se integra en Amoxcalli; catálogo de acepciones, formas, textos, glifos y fuentes en SQLite con migraciones aditivas. Laboratorio visible con pares de entrenamiento, curva y métricas históricas. Continuación de 250 pasos (`continued-unseen`): chrF++ 22,6 → 28,0 en 12 frases de validación. Auditoría de variantes: 2.157 registros sin variante, 1.687 propuestas `nci` sin aplicar. Importación determinista de 499 entradas de Molina vía GDN (sin LLM).

**30 sep · Lecturas y pipeline editorial.** Primer ciclo «flor» con plantilla de lección y auditoría editorial. `lesson_builder` publica 3 recorridos más (6 lecturas, 24 pasajes). `editorial_pipeline` prepara y publica por lotes: `batch-007-v9` añade 50 acepciones, 50 formas y 39 referencias; `batch-008-v10` y `batch-009-v11` quedan preparados y obsoletos por cambios de hash de las lecturas. `glyph_linker` v7 asocia referencias glíficas por reglas (99/523 entradas con referencia).

**7 oct · Propósito y nombre.** Dirección vigente: comprender fragmentos clásicos con fuente ([PROPOSITO.md](PROPOSITO.md)); propuesta de piloto institucional, no enviada ([PILOTO_INSTITUCIONAL.md](PILOTO_INSTITUCIONAL.md)); identidad editorial ([IDENTIDAD_EDITORIAL.md](IDENTIDAD_EDITORIAL.md)). El nombre visible pasa a Amoxcalli. Índice pictográfico de Tlachia (3 láminas). Ficha para taller. `lecturas-003` lleva el total a **12 lecturas, 48 pasajes de 10 obras y 28 preguntas de comprensión**. Comienza la iteración autónoma cada 30 min con diagnóstico, cola y estado persistentes (`iteration.py`).

**8 oct · Ciclos 004–011.** 311 apariciones pictográficas en 13 láminas (004). Batería documental: 123 consultas textuales + 51 visuales de desarrollo, reserva de 37 + 15 ([EVALUACION_DOCUMENTAL.md](EVALUACION_DOCUMENTAL.md), 005). Consulta documental medida: **119/123 completas, 840/860 campos, 2 abstenciones** ([CONSULTA_DOCUMENTAL.md](CONSULTA_DOCUMENTAL.md), 006). Comparación en el Laboratorio con los modelos declarados «sin ejecutar» (007) y caché validada de resúmenes: 2,1 s → 9 ms por acceso (008). Paquetes de revisión de la lectura Aves y su diagnóstico de vigencia (009–010, `lesson_review_packet`, `lesson_review_status`). Retorno al pasaje de origen desde Archivo y Diccionario (011).

**9–12 oct · Ciclos 012–016.** El retorno al pasaje llega al cotejo de fichas (012). Candidatos de conexión léxica: 8 pares elemento/forma para cotejo (013, `lexical_link_review`). Aves «disponible para estudiar» y primera separación entre entradas medidas y presentación (014). «Comparar aquí» dentro de una lectura (015). Preparación del candidato visual Qwen3-VL-4B: solo metadatos, sin descarga ni ejecución; propuesta de prueba local con imágenes, no autorizada (016).

**14 oct · Analizar cualquier palabra.** Analizador morfológico transparente (`morphology.py`), concordancia por raíz y pistas de glosa (`stems.py`): 77 % de segmentación exacta sobre 52 formas, 41,8 % de tokens clásicos con raíz enlazada ([MORFOLOGIA.md](MORFOLOGIA.md)). Primera suite completa en macOS; respuesta JSON 500 ante errores del servidor. Revisión práctica que da origen al [ROADMAP](ROADMAP.md): un clon nuevo fallaba 46 de 258 pruebas.

**15 oct · Preguntar y limpieza.** `#preguntar`: recuperación con evidencia, sin LLM; entrada correcta en primer lugar 92 % frente a 42 % de la búsqueda exacta ([EVIDENCIA.md](EVIDENCIA.md)). Explicaciones citadas, con validador de citas. Simplificación del proceso (este documento y la sección «Eliminado» del ROADMAP).

**16 oct · Fuentes abiertas.** Lote de Wiktionary (CC BY-SA, 3.215 lemas con revisión y licencia por ficha), notas gramaticales citadas de Carochi (1645, dominio público), ocho láminas más de Tlachia y borradores de permiso a la UNAM y para el Códice Florentino, sin enviar. Raíz enlazada: 41,8 % → 60,3 % de las palabras clásicas ([FUENTES.md](FUENTES.md), [ROADMAP](ROADMAP.md)).

## Qué se retiró y dónde quedó

| Retirado | Contenido | Ahora |
|---|---|---|
| `docs/PROGRESO_INTERNO.md` (9.600 palabras) | Registro por fecha | Este resumen; el plan en [ROADMAP.md](ROADMAP.md) |
| `docs/ITERACIONES.md`, `TRABAJO_AUTONOMO.md`, `LEARNING_ITERATION_PLAN.md`, `DIRECCION_APRENDIZAJE.md` | Método de iteración autónoma y planes anteriores | [ROADMAP.md](ROADMAP.md) · [PROPOSITO.md](PROPOSITO.md) |
| `docs/REVISION_LECTURA.md`, `ESTADO_REVISION_LECTURA.md`, `CANDIDATOS_CONEXIONES_LEXICAS.md`, `AUDITORIA_VARIANTES.md` | Guías de herramientas retiradas | Historial de git |
| `docs/AUTOTRAIN.md`, `MEJORAR.md`, `ESTADO_MODELO.md`, `PRUEBA_VISUAL_LOCAL.md` | Laboratorio LLM | [MODEL_CARD.md](../MODEL_CARD.md) · [LABORATORIO.md](LABORATORIO.md) · [ROADMAP.md](ROADMAP.md) |
| `reports/iterations/`, `reading-review*/`, `lexical-link-review/`, `learning-audit*/`, `variant-audit-*/`, `tests-*.txt`, `platform-ui-*.txt`, informes `*_2026-*.md` | Evidencia de cada ciclo | Historial de git (`git show 86c217f:reports/...`) |
| `reports/RESULTADOS.md` | Tabla de generación del 19 sep | [MODEL_CARD.md](../MODEL_CARD.md) |
| `reports/documentary-laboratory-display-v1.json` | Evidencia de pantalla con hashes de la interfaz | Suite DOM (`make test-ui`) |
