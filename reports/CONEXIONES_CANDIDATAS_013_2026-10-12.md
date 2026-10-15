# Candidatos de conexión léxica · ciclo 013

Fecha de cierre: **12 de octubre de 2026**. Este ciclo retoma la preparación interrumpida el 9 de octubre por límite de uso; la interrupción no cuenta como otra entrega. Implementación delegada serialmente a un único escritor; sin escritores concurrentes.

## Problema y resultado

El diagnóstico 012 registra 152 elementos pictográficos, 143 sin vínculos léxicos declarados. Esa ausencia no obliga a crear asociaciones. Se cierra una herramienta local pequeña, de biblioteca estándar, para preparar coincidencias entre la denominación catalogada de un elemento y una forma léxica pública. **Una coincidencia de escritura no prueba equivalencia de sentido ni lectura de toda la imagen.**

El [lote inmutable candidatos-013](lexical-link-review/candidatos-013/candidates.md) contiene JSON y Markdown. De **17 pares de escritura coincidente**, se excluyen **9** por acepción ya vinculada; quedan **8 pares, 8 elementos y 8 acepciones**. No se aplican enlaces ni se crea una cola editorial adicional. Los nueve vínculos publicados permanecen intactos.

| Denominación | Forma pública | Acepción | Apariciones disponibles / mostradas |
|---|---|---|---:|
| michin | lex-michin | sense-michin | 1 / 1 |
| nacayotl | lex-gdn-m2-152689 | sense-gdn-m2-152689 | 10 / 3 |
| xayacatl | lex-gdn-m2-168603 | sense-gdn-m2-168603 | 9 / 3 |
| mazatl | lex-mazatl | sense-mazatl | 4 / 3 |
| tonatiuh | lex-tonatiuh | sense-tonatiuh | 1 / 1 |
| tletl | lex-tletl | sense-tletl | 3 / 3 |
| ehecatl | lex-ehecatl | sense-ehecatl | 3 / 3 |
| xiquipilli | lex-gdn-m2-168711 | sense-gdn-m2-168711 | 2 / 2 |

Se conservan las diferencias documentales: **nacayotl** lleva denominación/glosa catalogada «cuerpo», mientras la acepción de Molina distribuida por GDN dice «cosa que pertenece ala carne.»; **xiquipilli** conserva «alforja, bolsa; ocho mil» en el catálogo y «costal, talega, alforja, o bolsa.» en la acepción. No se decide que cada acepción cubra los sentidos del elemento ni el valor contextual de sus componentes.

## Implementación y fuentes

[lexical_link_review.py](../nahuatl_local/lexical_link_review.py) reutiliza `CorpusStore` con un **filename temporal explícito** y `public_records()`. La lectura se limita a los bundles públicos distribuidos, el manifiesto editorial y su lote admitido, el catálogo pictográfico, el catálogo público de variantes/tareas y las dependencias de implementación declaradas. Las rutas se comprueban antes de abrir el store. No se abre la base privada de Voces ni CSV, batería/reserva, pesos, imágenes o URLs durante la preparación de candidatos.

La comparación usa originales exactos o **NFC + casefold + strip**, sin eliminar acentos, hacer aproximaciones, inferir morfología ni fundir homónimos/variantes. El ID procede del triple elemento/forma/acepción; el fingerprint conserva la evidencia completa. Solo la acepción ya declarada en `lexical_links` excluye su par; otra acepción homónima sigue disponible.

El JSON copia registros públicos completos y originales públicos de procedencia con hashes de archivo/fila, glosas, variantes, originales, estados, derechos y fuentes. Se corrigió un riesgo real en la versión iniciada: una fila original privada/retirada, o dependiente de un registro ahora oculto, podría reaparecer por compartir ID con una fila actual pública. El filtro nuevo impide copiar esa procedencia; las filas públicas actuales de este lote permanecen completas.

Los contextos son hasta tres apariciones por elemento, ordenadas por ID y deduplicadas por aparición. Conservan lectura atribuida, los valores reales —incluidas listas vacías—, página/zona, fila completa y hashes de fila/página, además del hash documental histórico. El total y los omitidos son explícitos. No es una selección semántica ni representativa.

Las fuentes siguen siendo las fichas locales de **Tlachia, UNAM**, con los responsables y atribuciones de cada documento, y las fuentes léxicas públicas identificadas en cada registro (**Molina**, mediado por **GDN** o **Online Nahuatl Dictionary**, según la ficha). El [JSON](lexical-link-review/candidatos-013/candidates.json) conserva sus IDs, URLs/localizadores, filas y hashes exactos. Los enlaces remotos no se consultaron ni se atribuye cotejo primario nuevo.

Cada candidato tiene revisión humana `pending`, revisor/fecha/decisión/notas vacíos y evidencia vacía. Las decisiones reales se anotan en otro archivo, fuera del paquete; la herramienta no las importa ni aplica. `training:false` y condiciones originales permanecen. La [guía nueva](../docs/CANDIDATOS_CONEXIONES_LEXICAS.md) incluye preparación, `--check`, repetición y el comando correcto `unittest discover` para esta carpeta de tests sin paquete Python.

## Pruebas y reproducción

Pasan **15 pruebas dirigidas nuevas**: ocho pares actuales/procedencia/campos pendientes, homónimos y variantes, exclusión solo por acepción vinculada, NFC/case/espacios sin quitar acentos, privacidad/retirada de formas/acepciones/fuentes y dependientes, originales ocultos, contextos ordenados/límite/deduplicación/hashes/valores vacíos, estabilidad de ID con cambio de evidencia, idempotencia, notas/miembros extra protegidos, fuentes obsoletas y falsificación semántica, cambio de fuente durante preparación, rutas privadas/externas/traversal, symlinks de fuente/miembro/ancestro y acceso real restringido a fuentes públicas con SQLite temporal explícito eliminado al terminar.

- [Primer log](tests-conexiones-013-first.txt): los 15 métodos no llegaron a sus aserciones porque el fixture asumía que existía `reports/lexical-link-review/`. Se corrigió creando esa carpeta pública en `setUpClass`; no se modificó el contrato de la herramienta.
- [Log satisfactorio](tests-conexiones-013-second.txt): 15 pruebas, `OK`.
- CLI real: [prepared](lexical-link-preparation-013.txt), [valid](lexical-link-validation-013.txt), [unchanged](lexical-link-repeat-013.txt).
- Diagnóstico [013](diagnosis-conexiones-013.txt) y [repetición](diagnosis-conexiones-013-repeat.txt).
- Aves 012: [verificación real](package-verification-conexiones-013.txt), `valid`.

No hubo tres fallos consecutivos de una misma condición ni bloqueo pendiente. No se repitieron las 68 pruebas del ciclo 012, mediciones de recuperación/Laboratorio, pruebas UI, llamadas a modelos ni entrenamiento. El diagnóstico reproduce sus validadores existentes; no reemplaza ni re-mide resultados.

## Preservación y congelación

Se conservan baseline013 y state-before013. Inventario JSON, cola JSON e inventario Markdown de **013, su repetición y 012 son idénticos en bytes**. El estado permanece idéntico al snapshot previo: IDs, notas, decisiones, historia, runs y snapshots se conservan, con reconciliación idempotente. La verificación calculada queda en [iteration-repeat-conexiones-013-2026-10-12.json](iteration-repeat-conexiones-013-2026-10-12.json).

Del baseline de **262 archivos**, solo cambia el append de `docs/PROGRESO_INTERNO.md`; los otros **261 archivos mantienen SHA-256**. Corpus, originales, permisos, guías/módulos anteriores, UI, batería/reserva, informes y paquetes históricos se conservan. Recuperación/Laboratorio/display mantienen exactamente los bytes del 012; Aves 012 conserva fuentes y validez. La nueva implementación/guía no entra en el manifiesto del diagnóstico 012 y no invalida sus gates.

Siguen **12 lecturas, 48 pasajes, 575 acepciones, 578 formas, 311 apariciones y 9 vínculos declarados**, los tres gates técnicos vigentes y **66 tareas humanas abiertas**. Los ocho candidatos no aumentan los vínculos publicados ni cierran revisión humana.

**Freeze y STOP de implementación.** El registro de preservación congela hashes del módulo, guía, tests y lote; no se continúa otro ciclo ni se publica externamente. README español/inglés quedan para el coordinador tras su verificación independiente. No hubo red de fuentes, acceso privado/pesos, modelos, entrenamiento, descargas, contactos, pagos, commits ni push.

Siguiente acción: revisión humana de Aves 012 y, si resulta útil, cotejo identificado de los ocho candidatos con sus fuentes/contextos y derechos por uso. Los paquetes conservan pendientes; la preparación técnica no acredita equivalencia, traducción, cotejo primario ni aprendizaje de personas.
