# Apariciones documentales · Iteración 004

Entrega local, 8 de octubre de 2026. El catálogo pasa de **91 a 311 apariciones**, en **3 conjuntos**, al incorporar nueve láminas de Telleriano-Remensis en cuatro lotes acotados. Supera la meta cuantitativa de 300 de `TRABAJO_AUTONOMO`; esto acredita preparación documental técnica, no revisión lingüística especializada ni comprensión probada con personas.

## Lotes y fuentes

Se reutilizó HTML comprobado por el coordinador, obtenido del índice oficial de Tlachia con HTTPS y certificados verificados. La implementación no consultó la red ni descargó imágenes. La caché copiada a `data/pictography-cache/` está ignorada por Git; los candidatos distribuidos conservan SHA-256 del HTML. Los análisis se atribuyen a Tlachia y Bertina Olmedo (INAH), como en las recetas previas.

| Lote | Láminas de Tlachia | Apariciones añadidas | Componentes | Total acumulado |
|---|---|---:|---:|---:|
| `tlachia-telleriano-385-24r-25r-v3` | [385_24r](https://tlachia.iib.unam.mx/telleriano/385_24r), [385_24v](https://tlachia.iib.unam.mx/telleriano/385_24v), [385_25r](https://tlachia.iib.unam.mx/telleriano/385_25r) | 86 | 170 | 177 |
| `tlachia-telleriano-385-25v-v4` | [385_25v](https://tlachia.iib.unam.mx/telleriano/385_25v) | 25 | 50 | 202 |
| `tlachia-telleriano-385-22r-23v-v5` | [385_22r](https://tlachia.iib.unam.mx/telleriano/385_22r), [385_22v](https://tlachia.iib.unam.mx/telleriano/385_22v), [385_23r](https://tlachia.iib.unam.mx/telleriano/385_23r), [385_23v](https://tlachia.iib.unam.mx/telleriano/385_23v) | 86 | 167 | 288 |
| `tlachia-telleriano-385-21v-v6` | [385_21v](https://tlachia.iib.unam.mx/telleriano/385_21v) | 23 | 59 | 311 |

Cada lote tiene receta, candidato e informe en `editorial/pictography-tlachia-telleriano-…`. Ninguno excede cien apariciones. Son **220 apariciones y 446 componentes nuevos**, sin excepciones ni conflictos. Los elementos compartidos (49, 31, 60 y 37 respectivamente) coinciden en todos los campos salvo la URL de evidencia de otra lámina. Se conserva la fila original, incluida su URL. No se añadieron equivalencias lingüísticas ni puentes léxicos nuevos.

## Resultado calculado

| Entidad | Total |
|---|---:|
| Conjuntos | 3 |
| Láminas | 13 |
| Zonas | 155 |
| Glifos | 297 |
| Personajes | 14 |
| Apariciones | 311 |
| Elementos por documento | 152 |
| Denominaciones distintas | 142 |
| Componentes en contexto | 613 |
| Puentes léxicos explícitos | 9 |

El análisis por elemento conserva denominación y valores por aparición como campos distintos. El catálogo final contiene 79 apariciones sin cita y 70 sin componentes; son ausencias explícitas del material, no campos rellenados mediante inferencia. No se fusionaron elementos entre documentos ni grafías distintas.

## Preservación y comprobaciones

`reports/iterations/iteration-004/publication-audit.json` registra conteos, IDs compartidos, hashes de HTML, candidatos y respaldos. Se comprobó para cada publicación que todas las filas anteriores de documentos, láminas, zonas, elementos y apariciones quedan idénticas y en el mismo orden. Cada respaldo público coincide byte por byte con el catálogo anterior. Repetir cada publicación devolvió `unchanged` y conservó los bytes del catálogo y del candidato.

Se cotejaron los campos lectura, citas, morfología, descomposición y parte no expresada de las 220 apariciones contra los artículos HTML seleccionados. El parser existente conserva el texto de estos campos con normalización de espacios HTML; excluye artículos lexicográficos GDN y no interpreta píxeles. No se detectaron marcas `?` o `*` en las lecturas nuevas; las marcas de las filas previas permanecen idénticas. Los componentes y los valores pasan la validación existente y el control de conflicto semántico. Esta revisión es estructural y de catálogo; no cotejo del manuscrito.

Permanecen intactos los hashes de `corpus/learning-v1.json` (12 lecturas / 48 pasajes), `docs/PROPOSITO.md` y `docs/TRABAJO_AUTONOMO.md`. Se conserva `training:false`, atribución y documento de las recetas previas. El progreso mantiene sus claves históricas. No se abrió la base privada de Voces ni se cambiaron pesos, splits de entrenamiento, pagos, permisos o publicación externa. No se detuvo ni reinició el servidor 8766. No se hizo commit.

## Pruebas

- **21 pruebas pasan**: `tests.test_pictography` y `tests.test_iteration`, en `reports/tests-pictografia-004-2026-10-08.txt`. Se corrigió una expectativa obsoleta que siempre exigía la tarea de ampliación: ahora depende del conteo respecto a 300 y comprueba además una meta superior al conteo actual. El fallo inicial se conserva en `reports/tests-pictografia-004-first-failure-2026-10-08.txt`.
- **9 grupos UI pasan** en `reports/platform-ui-pictografia-004-2026-10-08.txt`: inventario calculado, filtros, paginación, consulta por contexto, observación guiada, atribución/hash, ausencia de imagen, exportación pública y almacenamiento personal intacto, además de los flujos previos. Utiliza servidor y base sintéticos temporales. El bind inicial fue bloqueado por sandbox; la repetición autorizada automáticamente pasó. El registro inicial se conserva en `reports/platform-ui-pictografia-004-sandbox-2026-10-08.txt`.
- **Desconexión PASS** en `reports/offline-pictografia-004-2026-10-08.txt`: fallback de navegación y ausencia de caché de corpus, perfiles, aportaciones o solicitudes externas. No acredita instalación en teléfono.
- `iteration-004` se regeneró con el estado persistente existente, conservando decisiones, notas y snapshots. Se añadió un evento `local_publication` para estos cuatro lotes. Una repetición con las mismas fuentes conservó bytes de inventario, cola y estado; registro en `reports/iteration-repeat-pictografia-004-2026-10-08.json`.

## Próximo hito

La ampliación cuantitativa queda cubierta y su tarea técnica sale de la cola actual, manteniendo su historia. El siguiente trabajo es preparar la batería documental: 100 consultas textuales y 50 visuales de desarrollo, más una reserva independiente agrupada por entrada, pasaje o lámina antes del reparto. Las referencias deben proceder de fuente identificada, con incertidumbre, responsable y permisos explícitos. Medir después recuperación y presentar en el Laboratorio los métodos medidos o ausentes de forma reproducible. No hay todavía batería, recuperación medida sobre ella ni ejecución multimodal.

La revisión de una lectura por una persona competente y una prueba con principiantes siguen pendientes. La cantidad de apariciones no autoriza entrenamiento ni demuestra calidad lingüística, independencia de ejemplos visuales o utilidad pedagógica.
