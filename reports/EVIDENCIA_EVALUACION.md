# Evaluación de la consulta con evidencia

Sistema `evidence-root-v1` · conjunto `evidence-questions-v1` · partición `all`. Generado por `python3 -m nahuatl_local.evidence_evaluation`. Cero llamadas a modelos.

## 1. Resultado por partición

| Sistema | Partición | n | Entrada top‑1 | Entrada top‑3 | Con pasaje pertinente | Precisión de pasajes | Abstención falsa | Abstención correcta |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| exact_search | dev | 17 | 30% | 30% | 73.3% | 95.2% | 26.7% | 100% |
| exact_search | test | 32 | 42.3% | 42.3% | 75.9% | 84% | 24.1% | 33.3% |
| exact_search | all | 49 | 38.9% | 38.9% | 75% | 87.8% | 25% | 60% |
| evidence | dev | 17 | 90% | 90% | 100% | 99.2% | 0% | 100% |
| evidence | test | 32 | 92.3% | 92.3% | 100% | 96.4% | 0% | 33.3% |
| evidence | all | 49 | 91.7% | 91.7% | 100% | 97.5% | 0% | 60% |

## 2. Por tipo de consulta (todas las particiones)

| Tipo | n | Entrada top‑1 (base → evidencia) | Con pasaje pertinente (base → evidencia) |
|---|---:|---|---|
| abstain | 5 | — → — | — → — |
| inflected | 10 | 0% → 80% | 70% → 100% |
| question | 2 | 100% → 100% | 100% → 100% |
| spanish | 16 | 92.3% → 92.3% | 100% → 100% |
| variant | 16 | 0% → 100% | 50% → 100% |

## 3. Explicaciones con citas

Redactor `explain-cited-v1` (extractive): 46 de 46 explicaciones pasan la validación de citas (cada frase cita IDs de la evidencia y las formas entre «» aparecen en lo citado); 2.98 frases y 3.76 citas de media. Claude: not_run: usar --explain claude con credenciales (tiene costo); no se ejecutó en esta medición.

## 4. Fallos del sistema con evidencia

- `pájaro` (dev, spanish): entrada top‑1: acxoyatototl
- `atlan` (test, inflected): entrada top‑1: ninguna
- `michime` (test, inflected): entrada top‑1: ninguna
- `teléfono` (test, abstain): no se abstuvo — Etiqueta escrita antes de la primera corrida y conservada. El archivo sí traduce «teléfono» en pasajes de Morelos (huehcatlahtolaztli); mostrarlos no es un error.
- `automóvil` (test, abstain): no se abstuvo — Etiqueta escrita antes de la primera corrida y conservada. El archivo sí traduce «automóvil» (calmimilo, Morelos); mostrarlos no es un error.

## Límites

- Un pasaje es pertinente si la forma señalada (o, en la línea base, alguna palabra náhuatl del pasaje) contiene la raíz esperada según la clave laxa. Es una aproximación automática.
- El conjunto es pequeño y lo escribió el equipo técnico; las particiones separan desarrollo de prueba, no sustituyen la revisión de una persona experta.
- Construcción de índices: 3.95 s (sobre cachés derivados ya presentes). Tiempo medio por consulta: exact_search 119.32 ms, evidence 51.97 ms.
