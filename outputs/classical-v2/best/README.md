# Náhuatl clásico experimental — versión 2

Actualizado: 19 de septiembre de 2026. **No es un traductor validado.**

## Modelo y entrenamiento

Qwen3-0.6B, revisión `c1899de289a04d12100db370d81485cdf75e47ca`, adaptado mediante LoRA en q_proj/v_proj (r=8, alpha=16). Base congelada; 1,146,880 parámetros entrenables. No se preentrenó un LLM desde cero. Código y pesos del adaptador ejecutables localmente, sin API.

- CPU BF16, PyTorch 2.7.1+cpu; semilla 42; longitud máxima 192; learning rate 0,0002; acumulación 1.
- 400 pasos, 0.227 pasadas equivalentes sobre 1.759 ejemplos admisibles. Tiempo acumulado: 733.82 segundos en este entorno; no es una promesa para otro equipo.
- NLL de validación: 5.3952 → 3.7940, sobre 24 ejemplos fijos. Mejor checkpoint: paso 400, seleccionado por validación, no por prueba.
- `best/`: adaptador para inferencia; `last/`: pesos y estado del optimizador/aleatoriedad para reanudar. La base se descarga separadamente según README.

## Datos y evaluación

Axolotl/UNAM vía Comunidad Elotl. Solo registros `Classical Nahuatl` / `nci`: 5.627 pares tras filtrado/deduplicación; 2.248 entrenamiento, 2.066 validación, 1.313 prueba, separados por obra. De entrenamiento, 489 pares exceden la longitud y se omiten. No se verificó manualmente cada alineación ni la independencia entre antologías.

La reducción de NLL no mide fidelidad semántica. La comparación exploratoria de generación, sus límites y los comandos de reproducción están en `reports/RESULTADOS.md`. Los juicios gramaticales humanos siguen pendientes. Español es la única entrada implementada; inglés es una fase posterior.

## Uso previsto y límites

Investigación, inspección de corpus y borradores explícitamente experimentales. Puede repetir palabras, inventar formas y cambiar el sentido. Recuperar pasajes o enlazar un catálogo no valida una traducción, una lectura glífica ni una atribución a un códice. No debe publicarse una salida como traducción histórica verificada sin revisión especializada.

JEV es una capa opcional de evaluación remota, no este modelo. Las reglas locales no simulan JEV ni certifican corrección. No se realizaron llamadas autenticadas a TypeSafe.

## Licencias y trazabilidad

Base Qwen Apache-2.0; código/documentación originales MIT; distribución Elotl MPL-2.0. Los derechos por obra y edición/traducción requieren revisión. El adaptador no se relicencia como MIT y no se presenta como datos auditados para cualquier uso. Consulta `THIRD_PARTY_NOTICES.md`, `docs/FUENTES.md` y las licencias conservadas en `third_party/`.

`outputs/classical-v2/training-report.json` conserva configuración, pérdidas, revisiones y hashes del conjunto de entrenamiento/validación. `reports/download-all.json` registra hashes y URLs de descarga.
