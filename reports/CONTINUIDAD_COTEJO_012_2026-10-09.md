# Conservar la consulta y volver al pasaje durante el cotejo · ciclo 012

Iniciado el 8 de octubre y cerrado el 9 de octubre de 2026. Se retomó el mismo ciclo después de una interrupción por límite de uso; no se contabiliza otra entrega ni activación. Único escritor GPT-6.1 Sol / high. La preparación técnica mantiene pendientes la revisión lingüística y la prueba de comprensión con personas.

## Problema demostrado

La prueba real inicial de lectura, Archivo y retorno funcionó a 360 y 390 px: selector dentro del contenido, navegación estática, foco en el pasaje y sin desbordamiento horizontal. No se cambió CSS para corregir un defecto inexistente. [Baseline del teléfono emulado](iterations/iteration-012/amoxcalli-mobile-baseline-012.json).

Sí se demostró una pérdida de contexto en el recorrido **Aves → chachalaca → Archivo → «Consultar fichas y comparar originales»**. Desde `#investigar/chachalaca?from=leer&lesson=aves&passage=axolotl-14546`, el enlace fijo `#consultar` abría la consulta vacía y sin retorno al pasaje. [Evidencia anterior](iterations/iteration-012/amoxcalli-mobile-comparison-baseline-012.json), [captura](iterations/iteration-012/amoxcalli-mobile-comparison-before-012.jpg). Se eligió esta única carencia de la prioridad 3 del propósito, sin ampliar contenido por cuota.

## Cambio y fuentes

Se leyeron TRABAJO_AUTONOMO, PROPOSITO, PROGRESO_INTERNO, inventario/cola/estado 011 y contratos de consulta, recuperación, Laboratorio y expedientes. Antes de editar se guardaron [154 hashes públicos](iterations/baseline-012.json), el [estado previo](iterations/state-before-012.json) y snapshots de los tres informes vigentes. Los archivos UI previos fueron reconstruidos después de editar y verificados byte por byte contra esos hashes; se conservan como `learning.js.before` y `documentary.js.before`. No se presenta esta reconstrucción como una copia física anterior a la edición.

`learning.js` admite `consultar` en la misma resolución de origen público del ciclo 011. Solo acepta modo, lectura y pasaje únicos, pertenecientes al catálogo; orígenes duplicados, externos, malformados, desconocidos o de otra lectura siguen rechazados. El enlace de cotejo del Diccionario y del Archivo conserva la consulta **actual del input**, codificada con `encodeURIComponent`, junto con el origen válido. Escucha `input` y `submit` sin sustituir los handlers de búsqueda; no escribe progreso ni almacenamiento.

`documentary.js` muestra el retorno a la lectura/pasaje exactos, con fuente y localizador, y enfoca ese enlace. Sus enlaces a Archivo y a la búsqueda del Diccionario llevan la consulta actual, incluso cuando se edita sin enviar el formulario. Los enlaces de palabra en los resultados mantienen el mismo origen validado. Las entradas directas y las consultas vacías siguen funcionando. Las consultas con `?`, `#`, `/`, comillas, `&` y HTML se codifican y escapan; no se interpretan como parámetros de origen ni código.

La solución modifica solamente esos dos archivos UI. Conserva estilos editoriales, endpoint, ranking, campos/citas, filtros, exportaciones y navegación 011. No añade contenido, otro sistema de contexto ni respuestas a ejercicios. [Fuentes y pruebas congeladas por SHA-256](iterations/iteration-012/source-freeze.json).

## Pruebas

- [DOM/HTTP dirigido 360/390](tests-cotejo-012-final.txt): consulta vigente al pasar desde Archivo y Diccionario; IDs de fichas iguales al endpoint; resultado → Diccionario con origen; texto editado → Archivo; retorno exacto y foco en lector/guiado; ejercicios sin responder; rutas directas y orígenes inválidos; bytes de estudio intactos, **cero escrituras**, solo GET públicos. jsdom configura `innerWidth`/`matchMedia` y observa scroll sintético; **no mide geometría**.
- [Cinco grupos de continuidad 011](tests-continuidad-012-final.txt) pasan; [once grupos de interfaz](platform-ui-cotejo-012.txt) pasan y generan evidencia de Laboratorio con una base sintética. Las pruebas heredadas de propuestas usan exclusivamente su base temporal.
- [68 pruebas Python pertinentes](tests-cotejo-012-python.txt) pasan en 140,421 s: recuperación, diagnóstico, Laboratorio/caché y expedientes 009/010. No se modificaron esos módulos, guías ni fixtures.
- [Privacidad offline](offline-cotejo-012.txt), sintaxis JavaScript y validadores actuales de [recuperación](documentary-retrieval-validation-012.txt) y [Laboratorio](documentary-laboratory-validation-012.txt) pasan. La validación de cierre reproduce sin caché; los modelos permanecen `not_run`.

El coordinador comprobó en **navegador real**: el enlace de Archivo conserva chachalaca, devuelve tres fichas, muestra retorno enfocado y no desborda a 360 px (contenido/client 345) ni a 390 px (375). Editar a `atl` **sin enviar** y abrir Archivo conserva el texto actual y el origen 14546; el retorno activado con teclado enfoca ese artículo. [Evidencia final](iterations/iteration-012/amoxcalli-cotejo-browser-final-012.json), capturas [360](iterations/iteration-012/amoxcalli-cotejo-360-after-012.jpg), [390](iterations/iteration-012/amoxcalli-cotejo-390-after-012.jpg) y [retorno](iterations/iteration-012/amoxcalli-cotejo-return-012.jpg). Son viewports emulados, no teléfonos físicos ni una auditoría WCAG completa.

El primer intento de baseline DOM no pudo abrir localhost por el sandbox; [se conserva el error](tests-lectura-movil-012-baseline.txt). Con permiso local y base sintética, [continuidad previa pasó](tests-lectura-movil-012-baseline-localhost.txt). El primer y último test nuevo pasaron; el último añade `#` al caso de signos. No hubo tres fallos de una misma condición. El exit 1 del estado de Aves 011 expresa obsolescencia esperada, no un validador debilitado.

## Integridad y expedientes

Los dos hashes UI son entradas explícitas del informe de recuperación y exigieron una actualización de dependencias. Se midió una sola vez tras congelar y se conservó el snapshot. [14 comprobaciones](iterations/iteration-012/retrieval-preservation.json) confirman **123 respuestas y todos sus campos, IDs y auditorías idénticos**, excluidos solamente `seconds` por consulta; corpus, configuración, índice, batería y reserva conservan hashes. Se mantienen 119 completas, dos parciales, dos abstenciones y 840/860 campos exactos. Construcción 6,163 s, consultas acumuladas 0,856 s / media 6,959 ms, pico Python trazado 121.587.996 bytes; el coste excluye memoria nativa/proceso y fuentes precargadas. No se presenta como mejora de ranking o aprendizaje.

Se refrescaron solo los contratos/evidencias de Laboratorio requeridos. [Diagnóstico 012](iterations/iteration-012/inventory.md), cola y su repetición son idénticos en bytes. La [preservación calculada](iteration-repeat-cotejo-012-2026-10-09.json) conserva IDs, notas, decisiones y prefijos de historia/runs/snapshots; la reconciliación del estado es idempotente. De 154 archivos del baseline, solo cambian UI2, informes3, estado y el append de PROGRESO: **147 protegidos mantienen sus bytes**, incluidos corpus, originales, configuraciones, paquetes/informes históricos y módulos/pruebas 009/010. Permanecen 12 lecturas/48 pasajes, 575 acepciones/578 formas, 311 apariciones/nueve puentes, desarrollo 123/51, reserva 37/15 y **66 tareas humanas abiertas**; los tres gates están `ready`.

La entrega nueva [Aves 012](reading-review/aves-012/package.md) pasa [reconstrucción real](package-verification-cotejo-012.txt), preparación repetida `unchanged` y [estado vigente](reading-review-status/aves-012.md). Conserva cuatro pasajes, ocho preguntas ya existentes y cinco tareas con campos humanos vacíos/pending. Aves 011 y los paquetes 009 permanecen intactos; el [estado nuevo del histórico 011](reading-review-status/aves-011-012.md) enumera seis dependencias obsoletas, sin reemplazar su estado histórico ni sus notas.

## Límites y siguiente paso

El retorno mejora continuidad de lectura y cotejo; no demuestra comprensión, revisión lingüística, derechos nuevos o utilidad con principiantes. Falta una revisión humana de Aves con el paquete vigente, acuerdos y responsables; después, una tarea nueva y rúbrica con un facilitador antes de una prueba acompañada. El coordinador dejó además una hipótesis documental para un futuro ciclo separado: preparar candidatos de coincidencia literal entre denominaciones y formas públicas, manteniendo evidencia y decisiones pendientes. No se inicia aquí ni se crean vínculos automáticamente.

No hubo entrenamiento/inferencia, lectura de pesos o Voces privado, descarga de modelos, pagos, contactos, red de fuentes, publicación externa, commit ni push. La continuación del 9 de octubre cerró el mismo ciclo 012; README queda para el coordinador después del STOP del escritor.
