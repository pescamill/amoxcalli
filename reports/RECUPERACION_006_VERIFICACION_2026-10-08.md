# Verificación del coordinador · ciclo 006

Se reprodujeron las respuestas del informe final y se comprobaron directamente 8.498 campos devueltos contra sus filas originales, valores y hashes de fila/archivo. Las 123 consultas textuales de desarrollo recuperan 840 de 860 campos requeridos: 119 respuestas completas, dos parciales y dos abstenciones. No se evaluó la reserva ni se ejecutó un modelo. [Evidencia calculada](iterations/iteration-006/coordinator-verification.json).

El manifiesto del diagnóstico coincide con los archivos actuales. Los hashes de repetición coinciden; las fuentes congeladas en 005, las decisiones y los prefijos de historia, ejecuciones, notas y snapshots permanecen intactos. Quedan 66 tareas humanas y una técnica de Laboratorio. Estas comprobaciones no acreditan revisión lingüística.

En el navegador se consultó «agua» y se abrió `atl` en Diccionario, donde permanecen ejemplos y referencias visuales. No se guardaron palabras ni se cambió el progreso. La revisión visual detectó que el estilo inline de los campos largos no se aplicaba bajo la política de contenido de la aplicación. Se corrigió mediante CSS externo; tras recargar, el ancho visible y el del contenido coinciden: 1.265 px. El estilo calculado es `white-space: pre-wrap` y `overflow-wrap: anywhere`.

La suite previa a esta corrección ejecutó 224 pruebas con un fallo esperado heredado. Después de corregir CSS, pasan los diez grupos de interfaz y dos comprobaciones críticas de recuperación y validación; se actualizaron medición y diagnóstico. No se repitió la suite completa por el ajuste de presentación.

El servidor habitual se reinició con el mismo comando y configuración para cargar la API nueva; quedó disponible en `http://127.0.0.1:8766`. La medición y las pruebas de recuperación usan bases públicas temporales; el arranque normal de la aplicación conserva su persistencia habitual. No hubo entrenamiento ni publicación externa. Ambos README reflejan los resultados actuales.

Siguiente trabajo: presentar la comparación en Laboratorio con resultados medidos y métodos sin ejecutar declarados explícitamente. Permisos para imágenes, cotejo primario, revisión especializada y comprensión con principiantes continúan pendientes.
