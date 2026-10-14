# Diagnosticar la vigencia de un paquete de lectura

El comando `lesson_review_status` inspecciona **un paquete explícito** preparado por `lesson_review_packet`. Reúne las discrepancias que el verificador original comunica una a una. El paquete, las notas y las fuentes se conservan; no hay importación de decisiones ni cierre de tareas.

Desde la raíz del proyecto:

```sh
.venv/bin/python -m nahuatl_local.lesson_review_status --package reports/reading-review/aves-009-v1
.venv/bin/python -m nahuatl_local.lesson_review_status --package reports/reading-review/aves-009 --format md
.venv/bin/python -m nahuatl_local.lesson_review_status --package reports/reading-review/aves-009-v2 --output reports/reading-review-status/aves-009-v2.json
```

Sin `--output`, stdout contiene JSON determinista o Markdown en español mediante `--format md`. Con `--output`, la extensión `.json` o `.md` determina el formato del informe. Una salida ya idéntica se conserva; una salida editada, con notas o bytes distintos se rechaza y exige un nombre nuevo. La salida debe estar bajo `reports/`, fuera del paquete y de las fuentes protegidas. Los nombres `inventory.json`, `queue.json` y `state.json` están reservados. Se rechazan rutas privadas, `..`, salidas externas y enlaces simbólicos en archivos y ancestros.

| Estado | Significado | Código de salida |
| --- | --- | --- |
| `valid` | Archivos y fuentes vigentes; el `verify` original reconstruyó y confirmó **todo** el paquete | 0 |
| `stale` | Se encontraron únicamente fuentes cambiadas o ausentes; se enumeran todas | 1 |
| `invalid` | Problema de estructura, integridad, seguridad o reconstrucción semántica | 1 |

`ready` solo es `true` con `valid`. `semantic_validation` es `passed`, `failed` o `not_run`. Cuando existen discrepancias previas, no se reconstruye ni se emite aprobación parcial. Errores del destino de salida se comunican como excepción y tampoco permiten sobrescritura.

El informe enumera archivos obligatorios editados/ausentes, miembros extra, manifiesto inválido o no canónico, fuentes cambiadas/ausentes y hashes previos/actuales. Los campos, tipos, SHA-256 y nombres fijos del manifiesto son estrictos; campos JSON duplicados y constantes ajenas a JSON se rechazan. Un paquete editado junto con sus hashes recalculados solo puede obtener `valid` si coincide con la reconstrucción original. El propio manifiesto no aporta una firma ni una acreditación humana.

Antes de abrir fuentes se comprueban todas sus rutas. Las entradas de fuente desconocidas o inseguras solo se identifican mediante un índice, sin repetir rutas rechazadas. Los extras se cuentan como causas sin abrirlos ni copiar nombres o notas. Un preflight adicional comprueba las referencias internas del inventario, publicaciones y evidencias de decisiones históricas que abriría la reconstrucción heredada: una referencia desconocida bloquea `verify` antes de que pueda abrirla.

El registro admitido es **el contrato público del ciclo 009**: 61 rutas conocidas más las tres referencias de diagnóstico del paquete (`inventory.json`, `queue.json`, `state.json`). Se reconocen aparte ocho rutas de evidencia de decisiones históricas para comprobar su seguridad antes de reconstruir. No se buscan archivos por carpetas ni se sigue una URL. Un lote futuro con fuentes/evidencias nuevas exige revisar y ampliar explícitamente este registro y versionar el comando; no se promete admisión automática. La comprobación original sigue exigiendo que el inventario corresponda a las fuentes actuales.

Los informes incluyen solo metadata, IDs necesarios y hashes. No incluyen originales textuales, preguntas/claves, filas esperadas, reserva, contenido de decisiones ni notas de participantes. Tampoco acceden a Voces privado, pesos o modelos. La seguridad de rutas se verifica antes de cada lectura; como los paquetes originales, este flujo requiere un único escritor y no es una instantánea frente a cambios concurrentes.

Al 8 de octubre de 2026, `aves-009` muestra dos fuentes cambiadas (guía y módulo originales), `aves-009-v2` muestra una (guía) y la entrega autoritativa `aves-009-v1` reconstruye con éxito. Los históricos se conservan. El nuevo comando no convierte ningún paquete obsoleto en material vigente: regenerar en una carpeta nueva, conservar las notas previas y comprobar de nuevo los fingerprints.

La revisión humana sigue **pendiente**, incluso con `valid`. Las 66 tareas humanas actuales no se cierran. La igualdad de hashes acredita comparación de bytes; la revisión lingüística, los derechos por uso y la comprensión con personas necesitan evidencia y responsables conforme al [protocolo del piloto](PILOTO_INSTITUCIONAL.md). La [guía de preparación original](REVISION_LECTURA.md) continúa describiendo el paquete 009 sin modificaciones.
