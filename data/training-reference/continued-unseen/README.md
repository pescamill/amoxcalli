# Referencia del entrenamiento histórico

Esta carpeta permite consultar los pares asociados a `outputs/continued-unseen/run/best` sin ejecutar el modelo.

Los tres JSONL reproducen exactamente la preparación original (2.248 / 2.066 / 1.313 filas), verificada por los SHA256 registrados en `outputs/continued-unseen/automation.json`. Se reconstruyeron desde `corpus/axolotl/axolotl.csv`, con deduplicación y preparación anteriores a `nah-ortho-1`. No se reemplazó `data/prepared`.

`seen.json` conserva los 650 IDs recorridos, en orden, y los 1.759 admisibles al formato de 192 tokens. Proceden del orden y cursor del checkpoint local: 400 pasos heredados + 250 de continuación, acumulación de gradiente 1, mejor paso 250 igual a último. No se confunden los 2.248 preparados con los efectivamente recorridos. El manifest registra hashes de los tres splits, CSV original, lista de IDs y checkpoint.

Reproducción en un directorio nuevo, con dependencias/tokenizador/checkpoint locales:

```bash
.venv/bin/python scripts/reconstruct-training-reference.py --output /tmp/referencia-historica-nueva
```

El comando comprueba la correspondencia antes de escribir; no cambia pesos ni inicia entrenamiento. La plataforma solo necesita los archivos incluidos para mostrar los pares. Son alineaciones de Axolotl/Elotl, pendientes de revisión filológica propia. Se conservan atribución, licencia declarada del distribuidor y límites de derechos de cada edición; consultar `corpus/axolotl/README.md` y `THIRD_PARTY_NOTICES.md`.
