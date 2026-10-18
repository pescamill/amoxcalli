# Náhuatl clásico experimental — versión 2

> **Archivado el 16 de octubre de 2026.** El modelo ya no forma parte de la aplicación (ver [README](README.md)). Las rutas a módulos (`nahuatl_local.train`, `nahuatl_local.benchmark`…) corresponden ahora a `experiments.llm.*`; `reports/benchmark-*.json` está en `experiments/llm/reports/`; las referencias a «Laboratorio en Amoxcalli» describen la interfaz retirada.

Distribución Git: se conservan los adaptadores `best` e informes históricos; la base Qwen, los checkpoints `last` y los estados del optimizador quedan fuera del repositorio. Las instrucciones de reanudación exacta requieren esos archivos en la instalación local original. Un clon permite consultar la historia y probar los adaptadores tras descargar la base; no reconstruye el estado completo de entrenamiento.

Actualizado: 12 de octubre de 2026. **No es un traductor validado.** Los resultados de entrenamiento descritos siguen correspondiendo a los pesos existentes.

La ruta con imágenes está en preparación: Qwen3-VL-4B-Instruct no se ha descargado, ejecutado ni entrenado en esta iteración. Laboratorio permite inspeccionar 51 consultas documentales visuales de desarrollo, con referencias separadas de la entrada propuesta. Son consultas de catálogo, no una prueba de reconocimiento de píxeles. El preflight local detecta Transformers 4.51.3 sin `qwen3_vl`; no verifica inferencia ni consumo de memoria. La primera prueba local con imágenes está descrita en [docs/ROADMAP.md](../../docs/ROADMAP.md); sigue sin autorizar.

## Modelo y entrenamiento

Qwen3-0.6B, revisión `c1899de289a04d12100db370d81485cdf75e47ca`, adaptado mediante LoRA en q_proj/v_proj (r=8, alpha=16). Base congelada; 1,146,880 parámetros entrenables. No se preentrenó un LLM desde cero. Código y pesos del adaptador ejecutables localmente, sin API.

- CPU BF16, PyTorch 2.7.1+cpu; semilla 42; longitud máxima 192; learning rate 0,0002; acumulación 1.
- 400 pasos, 0.227 pasadas equivalentes sobre 1.759 ejemplos admisibles. Tiempo acumulado: 733.82 segundos en este entorno; no es una promesa para otro equipo.
- NLL de validación: 5.3952 → 3.7940, sobre 24 ejemplos fijos. Mejor checkpoint: paso 400, seleccionado por validación, no por prueba.
- `best/`: adaptador para inferencia; `last/`: pesos y estado del optimizador/aleatoriedad para reanudar. La base se descarga separadamente según README.

## Datos y evaluación

Los pesos del piloto se entrenaron sobre Axolotl/UNAM vía Comunidad Elotl, con registros `Classical Nahuatl` / `nci`: 5.627 pares tras filtrado/deduplicación; 2.248 entrenamiento, 2.066 validación, 1.313 prueba, separados por obra. De entrenamiento, 489 pares excedían la longitud y se omitían. El manifest histórico se conserva en `reports/corpus-preparation-legacy.json`. No se verificó manualmente cada alineación ni la independencia entre antologías.

La preparación actual en `data/prepared` contiene 5.462 pares (2.161/2.049/1.252), con normalización `nah-ortho-1`, proporción máxima de palabras 2,5 y estadísticas del tokenizador local. Estos datos no han producido nuevos pesos. Las métricas antiguas describen otra preparación y muestra; requieren una evaluación nueva para compararse. Las propuestas de variantes (`corpus/variant-proposals-v1.json`) todavía no forman parte de este conjunto.

La reducción de NLL no mide fidelidad semántica.

### Comparación exploratoria de generación (19 de septiembre de 2026)

Mismas 20 frases de prueba (semilla 2026), inferencia CPU greedy, máximo 96 tokens. RAG añade dos pasajes del conjunto de entrenamiento; el adaptador no se entrenó con ese formato. Red bloqueada durante cada evaluación.

| Condición | chrF++ (20) | chrF++ sin alertas de solapamiento (18) | Salidas al límite de 96 tokens |
|---|---:|---:|---:|
| Base sin adaptar | 15.36 | 14.65 | 0/20 |
| Adaptador, 400 pasos | 16.03 | 15.55 | 2/20 |
| Adaptador + contexto RAG | 22.44 | 17.97 | 6/20 |
| Devolver directamente el pasaje más cercano | — | 27.20 | No aplica |

chrF++ mide similitud textual, no porcentaje de traducciones correctas. La recuperación directa obtiene más similitud que el generador: no debe presentarse el ajuste como un traductor. Sin intervalos de confianza. Resúmenes en `reports/benchmark-*.json`; para regenerarlos (requiere `requirements.txt` y la base descargada):

```bash
python3 -m nahuatl_local.benchmark --output reports/benchmark-base-full.json
python3 -m nahuatl_local.benchmark --adapter outputs/classical-v2/best --output reports/benchmark-adapter-full.json
python3 -m nahuatl_local.benchmark --adapter outputs/classical-v2/best --rag --output reports/benchmark-adapter-rag-full.json
```
 Los juicios gramaticales humanos siguen pendientes. Español es la única entrada implementada; inglés es una fase posterior.

## Uso previsto y límites

Investigación, inspección de corpus y borradores explícitamente experimentales. Puede repetir palabras, inventar formas y cambiar el sentido. Recuperar pasajes o enlazar un catálogo no valida una traducción, una lectura glífica ni una atribución a un códice. No debe publicarse una salida como traducción histórica verificada sin revisión especializada.

JEV es una capa opcional de evaluación remota, no este modelo. Las reglas locales no simulan JEV ni certifican corrección. No se realizaron llamadas autenticadas a TypeSafe.

## Licencias y trazabilidad

Base Qwen Apache-2.0; código/documentación originales MIT; distribución Elotl MPL-2.0. Los derechos por obra y edición/traducción requieren revisión. El adaptador no se relicencia como MIT y no se presenta como datos auditados para cualquier uso. Consulta `THIRD_PARTY_NOTICES.md`, `docs/FUENTES.md` (en la raíz del repositorio) y las licencias conservadas en `third_party/`.

`outputs/classical-v2/training-report.json` conserva configuración, pérdidas, revisiones y hashes del conjunto de entrenamiento/validación. `reports/download-all.json` registra hashes y URLs de descarga.

## Continuación automática

La nueva ejecución y su configuración están en `outputs/automatic/MODEL_CARD.md` y `outputs/automatic/SUMMARY.md`. Las métricas anteriores describen el piloto de 400 pasos; no son las métricas de la continuación. El orquestador por etapas (`autotrain`) se retiró el 15 de octubre de 2026 (ver [docs/ROADMAP.md](../../docs/ROADMAP.md)); `python3 -m nahuatl_local.train` sigue disponible para una corrida nueva.


## Laboratorio en Amoxcalli

La navegación principal ofrece una explicación de Qwen/LoRA, curva y métricas históricas, informes descargables y pruebas locales. La implementación de las lecturas, glifos y laboratorio no entrenó nuevos pesos. Las métricas de la continuación de 250 pasos pertenecen a la preparación anterior; la aplicación comprueba los hashes y las distingue de la evaluación actual de recuperación. Guía: [LABORATORIO.md](LABORATORIO.md).
