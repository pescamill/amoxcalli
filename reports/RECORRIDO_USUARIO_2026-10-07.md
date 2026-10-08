# Recorrido de Scriptorium como lector

7 de octubre de 2026. Exploración por el agente mediante la interfaz local; no es una entrevista con estudiantes ni una revisión lingüística.

## Lo que invita a seguir

- La lectura `aves` conecta el mismo `tototl` con poesía y relatos. El primer ejemplo (`axolotl-14546`) despertó curiosidad por `chachalaca` y `tlatohua`, además de la palabra anotada.
- Buscar `chachalaca` en el archivo devolvió tres registros: `axolotl-14546`, `axolotl-14479` y `axolotl-10403`. El último contiene un fragmento más largo del poema. Las traducciones y grafías son las del archivo; no se dedujo una glosa nueva.
- Buscar `tototl` en el diccionario devuelve cuatro entradas. La entrada `çaquantototl` (`sense-gdn-m2-171054`) distingue claramente el apoyo visual relacionado de un glifo de toda la palabra.
- Buscar `ave canta` en el laboratorio, en modo recuperación, devolvió 34 coincidencias, con seis visibles. El primer resultado fue el poema de la lectura y aparecieron otros cantos de aves.
- Buscar `corazón` entre los 650 pares recorridos por el adaptador devolvió 25 pares. Las formas recurrentes y los contextos emocionales merecen una futura selección editorial de lecturas, previa revisión. El visor resulta interesante para leer, además de documentar entrenamiento.
- Mis palabras permite guardar `tototl` y practicar su recuerdo. Voces explica de forma clara permisos separados para publicación/entrenamiento y retiro de aportaciones.

## Fricciones observadas

1. **Continuidad tras una búsqueda sin resultados.** `chachalaca` y `tlatohua` no devolvieron entradas del diccionario. No se ofrece desde ese estado un enlace al archivo, aunque `chachalaca` sí tiene testimonios. Añadir una salida contextual evitaría que la exploración termine ahí.
2. **Reconocimiento frente a comprensión.** El primer ejercicio de `aves` permite elegir `tototl` mirando la forma visible, sin entender el fragmento. Con una respuesta incorrecta, la explicación además revela la respuesta. Conviene conservar ese ejercicio inicial y añadir una pregunta breve sobre el contexto.
3. **Prioridad de la coincidencia exacta.** Al buscar `tototl`, `çaquantototl` aparece antes que la entrada exacta. Dar prioridad a la forma exacta haría más directa la consulta.
4. **Una ficha guardada pierde el hilo del pasaje.** El repaso muestra significado y referencia visual, pero no el verso desde el que se guardó la palabra. Conservar el contexto de guardado ayudaría a volver a la lectura.
5. **Entrada a Voces.** Desde Aprender, Aportar pasa a una navegación llamada Investigar. El perfil contempla «Estoy aprendiendo» y «No sé cuál elegir todavía», pero la experiencia inicial seleccionada es «La hablo desde mi infancia».

## Estado dejado por la exploración

Se guardó `tototl`, se completó el primer ejemplo de `aves` y se marcó recordada en Mis palabras. No se creó un perfil ni se enviaron aportaciones lingüísticas. Se inició el servidor local y se dejó usando el lanzador normal del proyecto. La exploración no modificó código ni entrenó pesos.

## Prueba breve del generador

Se probó «El ave canta.» en el modelo local, primero sin contexto añadido. La salida fue «Yn otec.»; la interfaz registró 1,01 s de generación y recuperó el poema de `axolotl-14546` y el pasaje de `axolotl-08648` para contrastar. Ese tiempo de generación no necesariamente incluye toda la carga inicial. Esta observación no es una evaluación lingüística ni una medición representativa de rendimiento.

Se repitió la misma frase mostrando los dos ejemplos de referencia al modelo, con vista previa del contexto. La salida cambió a «Auh in ic uicuia.»; la interfaz registró 1,56 s de generación. Dos salidas diferentes no establecen una mejora de traducción: para juzgarla hace falta revisión competente. La vista previa sí ayuda a entender exactamente qué cambia entre los experimentos.

Siguiente mejora propuesta: cerrar el circuito lectura → palabra → otros testimonios → repaso con el fragmento original. Priorizar las palabras que ya despiertan preguntas dentro de las lecturas, antes de ampliar el inventario sin conexiones pedagógicas.
