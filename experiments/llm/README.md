# Laboratorio del LLM · archivado

Entre el 16 de septiembre y el 12 de octubre de 2026 Amoxcalli probó un traductor experimental español → náhuatl clásico: **Qwen3-0.6B ajustado con LoRA** (1.146.880 parámetros entrenables, base congelada, CPU), con y sin pasajes recuperados en el mensaje (RAG). El 16 de octubre de 2026 se retiró de la aplicación y su código se trasladó aquí, sin cambios de método. La aplicación (`nahuatl_local/`) no importa nada de esta carpeta ni carga PyTorch, Transformers o PEFT; `#modelos` muestra solo un resumen estático.

## Qué se midió

| Condición (mismas 20 frases de prueba) | chrF++ |
|---|---:|
| Modelo base, sin ajustar | 15,4 |
| Adaptador LoRA, 400 pasos | 16,0 |
| Adaptador + contexto recuperado (RAG) | 22,4 |
| **Devolver el pasaje más cercano (BM25), sin modelo** | **27,2** |

Pérdida de validación 5,40 → 3,79 en el piloto (400 pasos) y 3,578 → 3,530 en la continuación (250 pasos); en 12 frases de validación, chrF++ 22,6 → 28,0 con más repetición. Una salida registrada: «La casa y la flor.» → *Yn otlacuia yn otlacuia.* Detalle y límites: [MODEL_CARD.md](MODEL_CARD.md).

## Por qué no se usa

- La recuperación sola supera al generador y además cita su fuente; Preguntar ya responde con evidencia citada, sin modelo.
- El generador repite, cambia el sentido e inventa formas; ninguna salida tuvo revisión lingüística.
- No tenía función en el producto y exigía ~1,5 GB de pesos y dependencias de aprendizaje automático, frente a una aplicación de solo biblioteca estándar.
- Nunca se ejecutó sobre la batería documental actual; el candidato con imágenes (Qwen3-VL-4B-Instruct) no llegó a descargarse.

## Qué hay aquí

| Ruta | Antes | Qué hace |
|---|---|---|
| `train.py`, `runtime.py`, `evaluate.py`, `benchmark.py` | `nahuatl_local/` | Entrenamiento LoRA, carga e inferencia local, evaluación y banco chrF++ (con la línea base de recuperación) |
| `curate.py`, `training_data.py`, `review_labels.csv`, `reviewed.csv` | `nahuatl_local/`, `templates/` | Pares de entrenamiento: visor de referencia, propuestas de Voces, revisión y curación |
| `download.py` | `nahuatl_local/` | Descarga de la base Qwen y del corpus con revisiones fijadas |
| `model_status.py`, `laboratory.py`, `visual_preparation.py` | `nahuatl_local/` | Estado del modelo, resumen del Laboratorio y preparación del candidato con imágenes |
| `compose.py`, `review.py` | `platform.py`, `nahuatl_local/` | La antigua ruta `POST /api/compose` (reglas léxicas acotadas y borrador del LLM) y su ficha de revisión |
| `web/laboratory.js`, `web/training-data.js` | `platform_web/` | Pantallas Probar, Datos de entrenamiento y Modelo y progreso |
| `scripts/`, `configs/`, `requirements.txt` | raíz | Prueba HTTP del modelo, reconstrucción de la referencia de entrenamiento, configuraciones de entrenamiento y dependencias |
| `reports/` | `reports/` | Informes del banco, prueba de la web, preparación histórica, hashes de descarga y la última comparación documental del Laboratorio |
| `tests/` | `tests/` | Pruebas de estos módulos (las que necesitan PyTorch se omiten si falta) |
| `LABORATORIO.md`, `MODEL_CARD.md` | `docs/`, raíz | Guía del laboratorio y ficha del modelo, tal como estaban |

Fuera de esta carpeta siguen los pesos de los adaptadores (`outputs/`, versionados), la base descargada (`models/`, no versionada), la referencia de entrenamiento (`data/training-reference/`) y la preparación del corpus (`nahuatl_local/data.py`, que también usa el banco). Retirados sin archivar: `documentary_laboratory.py` (comparación del Laboratorio, sustituida por `make eval`) y las rutas `/api/laboratory*`; están en el historial de git.

## Volver a ejecutarlo

```bash
python3 -m venv .venv && .venv/bin/python -m pip install -r experiments/llm/requirements.txt   # Python 3.11/3.12
.venv/bin/python -m experiments.llm.download --only model
.venv/bin/python -m experiments.llm.benchmark --retrieval-only --split validation --output experiments/llm/reports/benchmark-retrieval-validation-current-full.json
.venv/bin/python -m unittest discover -s experiments/llm/tests -t .
```

Las pruebas de esta carpeta no forman parte de `make test` ni del CI (50 pruebas, 7 omitidas sin PyTorch, el 16 oct 2026). Para servir de nuevo un borrador habría que registrar `compose.make_compose` en el `Router` de `platform.py`; no está previsto.
