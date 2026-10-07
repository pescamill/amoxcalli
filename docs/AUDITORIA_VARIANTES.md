# Auditoría de variantes: fase 3

Fecha de investigación: 29 de septiembre de 2026. La auditoría cubre los 16.111 registros lógicos del CSV, incluidos los que contienen saltos de línea dentro de campos. Hay 2.157 registros con variante e ISO vacíos; no hay conflictos entre las etiquetas completas existentes.

Las propuestas y sus fuentes están en [variant-proposals-v1.json](../corpus/variant-proposals-v1.json). El [informe de revisión](../reports/variant-audit-2026-09-29/README.md), su `audit.json` y su `review.csv` conservan las cantidades, muestras, IDs, evidencia bibliográfica y huellas del original. Todas las decisiones iniciales son `pending`.

| Grupo | Filas | Propuesta | Decisión pendiente |
|---|---:|---|---|
| Diario | 1.483 | Classical Nahuatl / nci | Identificación de Chimalpahin; verificar edición precisa |
| Sexta Relación (Libro las ocho relaciones) | 160 | Classical Nahuatl / nci | Texto histórico de Chimalpahin |
| La llave del nahuatl | 44 | Classical Nahuatl / nci | Narración clásica de Sahagún reproducida por Garibay |
| Historia de México narrada en náhuatl y español | 245 | Sin ISO propuesto | Autoría moderna; confirmar registro lingüístico |
| Revista, estudios de cultura náhuatl | 199 | Revisión individual | El título mezcla artículos y textos de épocas distintas |
| El ajolote de Xochimilco | 15 | Localidad Milpa Alta documentada | Resolver correspondencia entre localidad e ISO |
| Adivinanzas nahuas | 10 | Sin ISO propuesto | Confirmar libro, edición y procedencia de todas las filas |
| Sin título | 1 | Sin etiqueta propuesta | Identificar fuente |

Las tres propuestas históricas abarcan **1.687 filas**; **470** siguen sin una propuesta de ISO. La fecha de una edición moderna no convierte un texto colonial en una variedad moderna. A la inversa, tratar un tema antiguo no demuestra que un texto moderno use náhuatl clásico.

## Reproducir la auditoría

```bash
.venv/bin/python -m nahuatl_local.variant_audit audit \
  --output reports/mi-auditoria-variantes
```

Usa un directorio nuevo. Se conserva la transcripción original; las grafías de comparación no sustituyen palabras del CSV. `source_sha256` identifica exactamente la revisión leída. Los IDs `axolotl-NNNNN` numeran registros CSV, no líneas físicas ni páginas de un libro.

## Aprobar una propuesta

Un responsable debe cotejar el informe y cambiar `decision` de `pending` a `approve` o `reject` en `review.csv`, completando `reviewer`. No cambies a mano la variante propuesta: una clasificación distinta requiere actualizar la evidencia y producir una auditoría nueva.

Después de esa revisión:

```bash
.venv/bin/python -m nahuatl_local.variant_audit apply \
  --audit reports/mi-auditoria-variantes/audit.json \
  --review reports/mi-auditoria-variantes/review.csv \
  --output data/curation/axolotl-variantes-revisadas.csv
```

El programa valida el hash del corpus, la cobertura de registros, sus IDs y las huellas de los campos. Solo propaga decisiones de obras con alcance `document`, evidencia y responsable. Rechaza grupos mixtos, etiquetas parcialmente existentes, títulos repetidos, cantidades incompatibles y cualquier sobrescritura. Escribe un CSV derivado y un manifiesto de cada cambio; el original se conserva.

La declaración del revisor no demuestra por sí misma un cotejo filológico. La clasificación tampoco cambia permisos de consulta, reproducción o entrenamiento.

## Uso posterior

El CSV derivado no sustituye el archivo consultable ni modifica `data/prepared`. Para preparar datos posteriores, utiliza una carpeta nueva y `--raw` explícito. Revisa primero derechos, alineaciones, alias de obras y relación con validación/prueba. Añadir una etiqueta no autoriza mover un pasaje reservado al entrenamiento ni comparar métricas de preparaciones distintas.

En los 199 registros de Revista, el próximo trabajo es recuperar título de artículo, autor y edición por fila. En Milpa Alta se debe conservar la localidad y resolver su clasificación con evidencia; copiar el ISO de otra obra perpetuaría la discrepancia. El registro sin título necesita identificación antes de cualquier propagación.
