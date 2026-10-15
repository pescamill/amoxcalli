# Segunda mejora: ampliación documental de Telleriano

7 de octubre de 2026. El lote `tlachia-telleriano-385-26v-v2` incorpora la lámina 385_26v del Códice Telleriano-Remensis, con etiquetas, valores, dudas y atribuciones de la página de Tlachia ya consultada. No es cotejo del manuscrito ni revisión lingüística.

## Problema corregido

`pictography_pipeline.publish` rechazaba un elemento existente si otra lámina del mismo documento aportaba una URL distinta. Ahora puede reutilizarse si todos los campos salvo `url` son idénticos. La fila original queda íntegra, incluidas URL y notas. Designación, significados, imagen, vínculos léxicos, notas y cualquier campo nuevo siguen sujetos a igualdad estricta.

## Resultado

| Medida | Antes | Añadido | Después |
|---|---:|---:|---:|
| Conjuntos documentales | 3 | 0 | 3 |
| Láminas | 3 | 1 | 4 |
| Zonas | 21 | 11 | 32 |
| Denominaciones distintas | 54 | 23 | 77 |
| Elementos por documento | 61 | 26 | 87 |
| Apariciones | 60 | 31 | 91 |
| Apariciones de componentes | 99 | 68 | 167 |
| Vínculos léxicos explícitos | 6 | 3 | 9 |

El candidato contiene 44 elementos: 18 se reutilizan y 26 son nuevos. No presenta excepciones. Reutiliza derechos, atribución, fila documental de Telleriano y vínculos léxicos explícitos del lote histórico v1. La receta v1 y su candidato permanecen como historia.

Todas las filas anteriores de documentos, láminas, zonas, elementos y apariciones se compararon íntegramente con el respaldo. El respaldo coincide con el candidato histórico v1. Repetir la publicación devolvió `unchanged` y mantuvo idénticos los bytes del índice.

Se conservan 6 lecturas, 24 pasajes, 575 acepciones y 578 formas. No se abrió ni modificó la base privada de Voces, ni se entrenó o descargó un modelo. Se reutilizó HTML local, sin nuevas consultas externas durante esta mejora.

## Archivos documentales

- Receta: `editorial/pictography-tlachia-telleriano-385-26v-v2.json`.
- Candidato: `editorial/pictography-tlachia-telleriano-385-26v-v2-candidate.json`.
- Informe de extracción: `editorial/pictography-tlachia-telleriano-385-26v-v2-candidate-report.json`.
- Caché local: `data/pictography-cache/telleriano-385_26v.html`, conservada fuera del versionado.
- Índice: `corpus/pictography/catalog.json`.
- Respaldo público: `corpus/pictography/catalog-before-tlachia-telleriano-385-26v-v2.json`.

SHA-256 del índice publicado: `879f051afced5c01a36bceb8a0e3563275253fec72cc973f83b5d965e68c1333`.

## Comprobaciones

```sh
.venv/bin/python -m nahuatl_local.pictography_pipeline \
  --recipe editorial/pictography-tlachia-telleriano-385-26v-v2.json \
  --cache data/pictography-cache \
  --output editorial/pictography-tlachia-telleriano-385-26v-v2-candidate.json \
  --publish corpus/pictography/catalog.json

.venv/bin/python -m unittest \
  tests.test_pictography tests.test_iteration tests.test_lesson_audit -v

npm run test:ui
npm run test:offline

.venv/bin/python -m nahuatl_local.iteration \
  --output reports/iterations/iteration-002 \
  --state reports/iterations/state.json
```

24 pruebas Python aprobadas. La ampliación a otra lámina prueba conservación de filas/notas, respaldo exacto, repetición idempotente y rechazo de cambios semánticos. UI y offline aprobados: se conservan tecpan/calli/chan, hashes, filtros, exportación pública, progreso personal y separación de datos privados. La prueba UI requirió permiso para su servidor efímero local; una primera expectativa intentó acceder a una función no expuesta en `window`, se corrigió y la corrida posterior pasó completa.

Las expectativas generales de los tests consultan conteos del fixture/API. La interfaz muestra `Alcance del registro inicial` cuando un documento tiene varias láminas y conserva su descripción original.

## Pendientes y siguiente tarea

El diagnóstico posterior conserva `iteration-001` y detecta su obsolescencia por el cambio de fuentes. Registra 78 elementos sin enlaces léxicos, 4 sin significados, 13 apariciones sin componentes, 37 sin citas y 18 componentes sin valores. No hay destinos léxicos rotos ni referencias de imagen ausentes. Estas cantidades describen el índice; no son instrucciones de completar datos sin evidencia.

Faltan 209 apariciones respecto a la meta documental propuesta de 300. La tarea técnica registra el lote realizado y sigue en progreso. Las revisiones de fuente, sentido, ejercicios y ensayo con personas conservan sus decisiones y bloqueos.

Limitación del primer diagnóstico: su cola técnica todavía no refleja la preparación de otras 6 lecturas para llegar a 12, ni la batería de evaluación textual/visual. La próxima mejora del diagnóstico debe añadir esos pasos verificables para que el coordinador tenga trabajo técnico sustentado además de ampliar el índice. No se implementó ese alcance en este lote.
