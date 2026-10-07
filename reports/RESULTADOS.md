# Resultados medidos — 19 de septiembre de 2026

**Se entrega un prototipo que funciona localmente, con pesos entrenados y recuperación de pasajes. El generador todavía no es un traductor fiable.** No hubo evaluación lingüística por especialistas ni llamadas autenticadas a JEV.

## Entrenamiento

Qwen3-0.6B + LoRA: 1,146,880 parámetros entrenables. CPU BF16, semilla 42, longitud 192, acumulación 1, learning rate 0,0002. Se completaron **400 pasos**, equivalentes a **0.227 pasadas** por 1.759 pares admisibles. No es una época completa. Tiempo acumulado medido: 733.82 s (~12.2 min); el rendimiento depende del hardware.

NLL ponderada por tokens sobre 24 ejemplos fijos de validación: **5.3952 → 3.7940**. El mejor checkpoint fue el paso 400. Se eligió por validación antes de medir prueba. Esta reducción no demuestra fidelidad semántica ni generalización.

## Comparación exploratoria de generación

Mismas 20 frases de prueba, semilla 2026: 2–15 palabras españolas normalizadas, hasta 25 palabras náhuatl. Inferencia CPU float32, greedy, máximo 96 tokens, penalización de repetición 1,1. RAG añade dos pasajes del conjunto de entrenamiento; el adaptador no fue entrenado con ese formato de contexto. Las conexiones de red estuvieron bloqueadas durante cada evaluación.

| Condición | chrF++ (20) | chrF++ sin alertas de solapamiento (18) | Salidas al límite de 96 tokens |
|---|---:|---:|---:|
| Base sin adaptar | 15.36 | 14.65 | 0/20 |
| Adaptador, 400 pasos | 16.03 | 15.55 | 2/20 |
| Adaptador + contexto RAG | 22.44 | 17.97 | 6/20 |
| Devolver directamente el pasaje más cercano | — | 27.20 | No aplica |

chrF++ mide similitud textual, **no porcentaje de traducciones correctas**. La recuperación directa no traduce entradas nuevas: solo devuelve texto existente y sirve como control. En este pequeño conjunto obtiene más similitud que el generador, lo que desaconseja presentar el ajuste como un traductor listo. No se calcularon intervalos de confianza ni significación.

La auditoría marca un ejemplo cuando su español o náhuatl alcanza semejanza de secuencia de palabras ≥0,65 con algún par de entrenamiento. Dos de veinte quedaron marcados. Los 18 restantes no están demostrados independientes: antologías, paráfrasis y variantes ortográficas pueden ocultar solapamientos. Las cifras son exploratorias y no deben reutilizarse para seleccionar repetidamente configuraciones.

La inspección de salidas muestra repetición de expresiones y pérdida de contenido. Por ejemplo, en `axolotl-03726` el adaptador sin RAG omite los nombres propios de la entrada; otras salidas repiten `in tlatocan`. Esa observación basta para mantener los borradores sujetos a revisión, aunque mejore una métrica agregada.

## Reproducir y continuar

```bash
python -m nahuatl_local.benchmark --output reports/benchmark-base-full.json
python -m nahuatl_local.benchmark --adapter outputs/classical-v2/best --output reports/benchmark-adapter-full.json
python -m nahuatl_local.benchmark --adapter outputs/classical-v2/best --rag --output reports/benchmark-adapter-rag-full.json
python -m unittest discover -s tests
```

Los informes JSON resumidos conservan IDs, hash del test, selección, tiempos y firma de SacreBLEU 2.5.1. Los comandos regeneran predicciones completas localmente. El ZIP omite esos textos completos y el corpus; el descargador reproduce la revisión fijada. El informe de entrenamiento conserva los hashes de entrenamiento y validación.

**Nueve pruebas técnicas pasaron**: particiones/deduplicación, codificación, contrato JEV sin red, revisión local, reanudación exacta en un modelo diminuto, recuperación de checkpoint interrumpido e interfaz/consulta local. No son nueve pruebas de competencia lingüística.

La exportación JEV funciona sin red. El envío opcional por API y CUDA/MPS no fueron probados aquí. El modelo base y los datos se descargan una vez; inferencia, búsqueda y entrenamiento posteriores son locales.

El próximo experimento es revisar alineaciones y errores con un especialista, continuar de forma controlada y evaluar en validación. No se debe usar una puntuación de JEV como verdad de entrenamiento. Consulta `docs/MEJORAR.md`; inglés y la alineación verificada por página/folio siguen pendientes.
