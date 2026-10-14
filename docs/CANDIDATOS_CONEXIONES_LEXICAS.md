# Candidatos documentales para revisión léxica

La coincidencia entre una denominación de elemento pictográfico y una escritura léxica ayuda a preparar una revisión. **No prueba equivalencia de sentido ni lectura de toda la imagen.** La herramienta no aplica vínculos, publica datos, cambia permisos ni usa un modelo.

```sh
.venv/bin/python -m nahuatl_local.lexical_link_review \
  --output reports/lexical-link-review/candidatos-013
.venv/bin/python -m nahuatl_local.lexical_link_review \
  --output reports/lexical-link-review/candidatos-013 --check
.venv/bin/python -m unittest discover -s tests -p 'test_lexical_link_review.py' -v
```

Se usa `CorpusStore` sobre una base **temporal explícita** y `public_records()`, junto con el catálogo pictográfico validado. No se abre la base privada de Voces, el CSV, la batería/reserva, imágenes ni URLs. Las fuentes públicas concretas se comprueban antes de instanciar la base temporal; se rechazan rutas privadas, `..` y enlaces simbólicos antes de leer o escribir.

La comparación admite escritura original exacta o `NFC + casefold + strip`. NFC permite comparar la misma letra con acento combinado o precompuesto, pero no elimina acentos; `strip` solo afecta espacios exteriores en la clave auxiliar. No se infiere morfología, traducción, especie, número, significado contextual ni equivalencia entre variantes. Los originales se conservan completos.

Cada par elemento/forma/acepción tiene ID estable y fingerprint. Se conservan todas las acepciones homónimas y todas las formas coincidentes. Solo se excluye el par cuando esa acepción ya está en `lexical_links` del elemento; otra acepción de la misma escritura sigue siendo candidata. Una forma, acepción o fuente retirada/privada y sus dependientes quedan fuera.

El JSON mantiene filas públicas completas de elemento, forma, acepción y fuentes; filas originales públicas de procedencia, hashes de archivo/fila, glosas/denominaciones separadas, variantes, localizadores, estado de verificación y condiciones de uso. Una versión original privada o retirada, o dependiente de una fuente actualmente oculta, no se vuelve a copiar por compartir ID con una fila pública actual. La procedencia distingue el hash de la **fila pública reconstruida** del de las **filas originales distribuidas**; no atribuye las actualizaciones del índice a la fuente primaria.

El contexto incluye hasta **tres apariciones por elemento, ordenadas por ID**, con filas completas, lectura atribuida, valores reales del componente, lámina/zona y hash de página histórico. Informa el total y cuántas quedan omitidas. La selección organiza una revisión inicial; no es muestreo representativo ni favorece una interpretación. La ausencia de valores permanece visible. No se copian imágenes.

`candidates.json` y `candidates.md` se escriben exclusivamente en una carpeta nueva bajo `reports/lexical-link-review/`. Repetir con idénticas fuentes devuelve `unchanged`; `--check` reconstruye el lote entero y confirma ambos archivos. Cambios de fuente, relaciones, IDs o notas provocan rechazo: nunca se sobrescribe un expediente editado. Se debe preparar una carpeta nueva y conservar las anteriores.

Cada candidato empieza con `human_review.status: pending` y revisor/fecha/decisión/evidencia/notas vacíos. La revisión real se anota **en un archivo aparte**, fuera de la carpeta inmutable. Debe identificar responsable, evidencia, contexto y alcance del vínculo propuesto. La herramienta no importa ni aplica esas decisiones; una asociación admitida requiere el flujo editorial y autorización apropiados, sin dar por aprobados usos o entrenamiento. `training:false` se conserva.
