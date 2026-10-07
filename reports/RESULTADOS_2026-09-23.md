# Continuación local — 23 de septiembre de 2026

**Resultado:** hay un adaptador entrenado aquí, ejecutable localmente. Es un generador experimental de borradores español → náhuatl clásico; su corrección histórica y lingüística no está demostrada. Sin API externa ni generación de etiquetas sintéticas.

## Datos y entrenamiento

Partimos del piloto Qwen3-0.6B + LoRA de 400 pasos CPU BF16. De los 2.248 pares etiquetados para entrenamiento, 1.759 caben en la longitud de 192 tokens. Al probar una continuación CPU float32 con optimizador nuevo se detectó que los 300 pasos adicionales del primer intento (`outputs/automatic`) volvían a leer los primeros 300 ejemplos del mismo orden ya consumidos por el piloto. Se verificó comparando sus permutaciones y cursores guardados. Esto puede contribuir al deterioro, pero no establece una causa única.

La continuación corregida (`outputs/continued-unseen`) hereda del piloto el orden, el cursor 400 y el generador de barajado; su checkpoint mejor completa 250 pasos adicionales, con cursor 650. Los 250 índices adicionales no estaban entre los 400 ya usados. Se reinició el optimizador al cambiar a float32, de modo que esto conserva pesos y cobertura de datos, no una trayectoria numérica exacta. Sigue disponible el estado completo del nuevo optimizador en `run/last`.

| Ejecución | Pares nuevos tras piloto | Mejor paso adicional | NLL validación, 128 pares | chrF++ validación, 12 frases | Truncadas, 12 | Trigramas repetidos, 12 |
|---|---:|---:|---:|---:|---:|---:|
| Piloto 400 | — | — | 3,5783 con esta configuración | 22,58 | 0 | 0,000 |
| Primera continuación, descartada | 0 en 300 pasos nuevos | 250 | 3,5173 | 16,56 | 3 | 0,259 |
| Continuación con cursor heredado | 250 | 250 | 3,5302 | 27,96 | 0 | 0,028 |

NLL menor no garantizó mejor generación. El filtro local sugiere la continuación corregida porque su chrF++ en validación aumentó, no se truncaron más salidas y la repetición media subió menos de 0,05. El filtro no reemplaza una revisión lingüística.

## Prueba exploratoria de generación

Mismas 20 frases de `test`, mismos IDs y hash SHA-256 `c02edc9f30f68bc1447504c08edcfb08a88207eca27bda32751bf43746053833`, inferencia sin RAG, CPU float32; máximo 96 tokens. Esta muestra se había inspeccionado ya al evaluar el piloto y la primera continuación. **No constituye evaluación ciega ni debe guiar nuevos ajustes al modelo.** Dos pares tienen una alerta de semejanza con el entrenamiento; los otros 18 tampoco garantizan independencia por obras.

| Adaptador | chrF++ 20 | chrF++ 18 sin alerta | Truncadas 20 | Trigramas repetidos, media 20 |
|---|---:|---:|---:|---:|
| Piloto 400 | 16,03 | 15,55 | 2 | No medido entonces |
| Primera continuación | 9,54 | 8,17 | 12 | 0,528 |
| Continuación con cursor heredado | 20,34 | 19,05 | 1 | 0,091 |
| Pasaje existente más cercano, control | — | 27,20 | No aplica | No aplica |

chrF++ mide similitud de caracteres/palabras con la referencia, **no porcentaje de traducciones correctas**. El control que recupera un pasaje existente no traduce un texto nuevo y superó al generador. Las salidas pueden repetir frases y omitir información; una persona competente debe revisar nombres, fechas, variantes y gramática. Los enlaces glíficos disponibles cubren coincidencias exactas de unas pocas palabras y no acreditan que una oración ni un folio concreto estén alineados. El inglés como idioma de entrada no está entrenado.

## Uso y reproducción

```bash
bash scripts/autotrain.sh --budget-minutes 60
.venv/bin/python -m nahuatl_local.serve --adapter outputs/continued-unseen/run/best
.venv/bin/python -m nahuatl_local.autotrain --output outputs/continued-unseen --budget-minutes 60
```

La primera orden instala y descarga la base (~1,50 GB) y el corpus fijados si faltan; cuando estén presentes, entrenamiento e inferencia no requieren red. La tercera continúa **el entrenamiento que se realizó aquí** con su estado guardado en la misma máquina o en otra CPU float32 compatible. Para crear una ejecución adaptada a otro hardware, consulta `docs/AUTOTRAIN.md`. El formulario JEV exporta preguntas acotadas; el revisor local determinista no es un modelo JEV y no se hicieron llamadas JEV para estos resultados.

Las evidencias compactas están en `outputs/{automatic,continued-unseen}/SUMMARY.md`, los informes `run/last/progress.json`, las métricas `reports/benchmark-{adapter,automatic-best,continued-unseen}.json` y los hashes guardados en `automation.json`. El ZIP excluye los JSON con textos completos de prueba y los archivos originales del corpus; se reproducen descargando las revisiones fijadas. Licencias y derechos por obra: `THIRD_PARTY_NOTICES.md`.
