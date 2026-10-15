# Aprender comparando · 015 · 12 de octubre de 2026

Las palabras para explorar abrían el Archivo y separaban a la persona del pasaje. Ahora **Comparar aquí** muestra hasta dos otros fragmentos dentro de la lectura, con original náhuatl, español ocultable, obra/variedad/localizador y fuente/estado. Los botones y búsqueda completa anteriores siguen disponibles; el enlace al Archivo conserva el origen del pasaje actual.

Se reutiliza `/api/research` sobre náhuatl clásico/histórico, con ventana acotada de diez resultados. La selección excluye el ID actual, deduplica registros y exige palabra completa con NFC/case, sin quitar acentos, recortar raíces ni aceptar subcadenas de compuestos/nombres. No convierte el total del API en un conteo exacto. Estados accesibles de carga/error/vacío y rechazo de respuestas tardías protegen cambios de palabra/ruta; no guarda progreso ni usa modelos/cachés privados.

La comparación real de **chachalaca** desde 14546 muestra los registros **14479** y **10403**, con traducciones inicialmente ocultas. Los registros pueden repetir texto: 10403 contiene el pasaje actual dentro de un fragmento mayor. La selección no demuestra independencia de testimonios, otra acepción ni comprensión de una persona.

Pasan **13 grupos DOM/HTTP en una sola corrida**, incluido el nuevo flujo: originales/fuentes/toggle, NFC/acento/palabra frente a compuesto, variedad, exclusión actual/deduplicación/límite, HTML escapado, error/vacío, carreras de respuestas/input/ruta, navegación con retorno y cero escrituras de almacenamiento. También pasan sintaxis JS y la validación real de Lab al fijar su evidencia. [Log único](tests-comparando-015.txt).

Recuperación conserva exactamente sus bytes del 014; no se mide otra corrida ni se repiten las 20 pruebas Python. Lab solo actualiza el hash de evidencia de presentación; sus métricas/costes y demás contenido permanecen iguales. Corpus, cuatro pasajes/ocho claves de Aves, otras once lecturas, edición compatible, decisiones y estado editorial conservan sus hashes. [Baseline acotado](baseline-comparando-015.json); [integridad/freeze](freeze-comparando-015.json).

**Freeze y STOP.** README/guías generales y verificación de navegador corresponden al coordinador. No se crea diagnóstico ni expediente nuevos. Revisión lingüística y ensayo de comprensión con personas siguen pendientes. Sin contenido nuevo, corpus modificado, entrenamiento, modelos, casos reservados, red externa, fuentes remotas consultadas, pesos/base privada, contactos, publicación, commits o push.
