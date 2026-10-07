# Primera experiencia de lectura y diccionario glífico

Entrega local del 29 de septiembre de 2026. El usuario eligió aprender náhuatl mediante ejemplos y precisó que las imágenes deben ser glifos asociados a palabras de las fuentes ya registradas. La aplicación no incorpora ilustraciones generadas.

## Resultado

- Navegación principal: Aprender, Leer, Diccionario y Mis palabras; Voces continúa en Aportar.
- Tres lecturas clásicas con doce fragmentos de La tinta negra y roja, tomados del archivo Axolotl existente. La transcripción y traducción se preservan; las anotaciones son explícitas y se verifican contra la grafía del fragmento.
- Ayuda al pulsar palabras, traducción ocultable, comprensión de fragmentos y recuperación de una forma exacta. La cuarta actividad de cada lectura utiliza otro ejemplo. Las claves son locales; el LLM no corrige ejercicios.
- Palabras guardadas y repaso con recuerdo declarado por el usuario. Progreso local al navegador, separado de perfiles, voces y aportaciones.
- Diccionario de **24 acepciones y 27 formas**, con **22 referencias visuales y 21 imágenes de fuente**, asociadas a 21 acepciones. El catálogo conserva 19 fuentes, 3 fichas textuales y 1 nota: 96 registros editoriales.
- Archivo completo de 16.111 pares, fuentes, extracción, exportación y laboratorio del modelo accesibles desde Archivo y herramientas.

## Palabras añadidas y sus testimonios visuales

Las formas y definiciones se contrastaron con las fichas del Online Nahuatl Dictionary, enlazando Molina cuando la ficha ofrece la entrada concreta. Las imágenes y el análisis contextual proceden de las fichas VLA de Stephanie Wood. Se reutilizan las fuentes registradas, conservando `catalog_checked`, asociación propuesta y `rights.training=false`.

| Forma | Acepción | Fuente visual | Ficha |
|---|---|---|---|
| tochtli | conejo | Mendoza 46r, elemento de Tochtepec | [VLA](https://aztecglyphs.wired-humanities.org/content/tochtli-mdz46r) |
| mazatl | venado | Mendoza 13v, elemento de Mazatlan | [VLA](https://aztecglyphs.wired-humanities.org/content/mazatl-mdz13v) |
| itzcuintli | perro | Mendoza 16r, elemento de Itzcuintepec | [VLA](https://aztecglyphs.wired-humanities.org/node/694) |
| tototl | ave | Mendoza 46r, elemento de Tototepec | [VLA](https://aztecglyphs.wired-humanities.org/content/tototl-mdz46r) |
| michin | pez | Mendoza 46r, elemento de Michapan | [VLA](https://aztecglyphs.wired-humanities.org/content/michin-mdz46r) |
| coatl | serpiente | Mendoza 7v, elemento de Coaixtlahuacan | [VLA](https://aztecglyphs.wired-humanities.org/content/coatl-mdz7v) |
| tlalli | tierra | Mendoza 32r, elemento de Tlalatlauhco | [VLA](https://aztecglyphs.wired-humanities.org/content/tlalli-mdz32r) |
| tletl | fuego | Mendoza 13r, iconografía de conquista | [VLA](https://aztecglyphs.wired-humanities.org/content/tletl-mdz13r) |
| ehecatl | viento | Mendoza 12r, elemento de Ecatepec; ficha titulada Ecatl | [VLA](https://aztecglyphs.wired-humanities.org/content/ecatl-mdz12r) |
| citlalin | estrella | Mendoza 17v, elemento de Citlaltepec | [VLA](https://aztecglyphs.wired-humanities.org/content/citlalin-mdz17v) |
| tepetl | cerro | Mendoza 32r, elemento de Ocotepec | [VLA](https://aztecglyphs.wired-humanities.org/content/tepetl-mdz32r) |
| metl | maguey | Mendoza 10r, elemento de Metepec | [VLA](https://aztecglyphs.wired-humanities.org/content/metl-Mdz10r) |

Eecatl se conserva como grafía adicional de Molina, separada del lema ehecatl. Piedra recibe una referencia visual del Mendoza 48r, conservando la existente del Xólotl. Se completaron las imágenes de árbol, sol, luna y mes mediante sus fichas existentes. **Ver, y/con y madera** siguen sin un vínculo visual específico incorporado: el índice muestra esa ausencia.

Los glifos y los fragmentos alfabéticos pertenecen a documentos diferentes. La ayuda los asocia por acepción y lo indica expresamente; no representa las frases como secuencias de glifos. Fuego permanece clasificado como iconografía, y las funciones de tepetl y Ecatl/Ehecatl conservan su contexto.

## Procedencia y migración

- `corpus/glyph-lexicon-v5.json`: 38 registros nuevos, importación aditiva e idempotente. No reemplaza IDs existentes.
- `corpus/glyph-source-images-v5.json`: completa campos ausentes de cuatro fichas, sin sobrescribir imagen, crédito, contexto ni ediciones locales.
- `corpus/learning-v1.json`: selección explícita de doce filas, hash del par, anotaciones y ejercicios.
- `nahuatl_local/learning.py`: valida fuente, etiqueta nci, intervalos y claves; oculta lecturas cuyos registros dependientes dejaron de ser públicos.
- `data/backups/voces-before-glyph-lexicon-v5.sqlite3`: respaldo privado previo a la migración, con permisos de archivo 0600.

Se compararon las 58 fichas anteriores con el respaldo: conservan sus contenidos salvo los campos añadidos por la migración declarada. Las tablas people y contributions de Voces son idénticas al respaldo. El CSV original conserva SHA256 `ed8e85f560e78c43385f91ac99d08dee071183749bc1f1aa1b88f1b3a2530878`. No se aplicó el lote pendiente de etiquetas de variantes ni se modificaron pesos o datos preparados.

## Comprobaciones

- Suite Python: **135 pruebas, OK con 1 fallo esperado** de una regla ortográfica deshabilitada. Informe: `tests-learning-glyphs-2026-09-29.txt`.
- Prueba DOM (`tests/platform_ui.cjs`) con jsdom en `/tmp`, base y servidor temporales: lectura, ayuda contextual, respuesta incorrecta/correcta, forma ocultada, finalización, palabras guardadas, repaso, búsqueda, filtros, aportación y retirada, fuentes y reglas heredadas. Sin errores de aplicación.
- Navegador real: portada y diccionario; **las 21 imágenes cargaron con dimensiones naturales válidas**. Se comprobó palabra/glifo/folio en tochtli.
- Pantalla de 390 px: ayuda contextual, guardado, avance, recarga con progreso conservado, cuaderno y repaso. Sin desbordamiento horizontal en las vistas comprobadas.

## Límites del piloto

La selección y las ayudas son borradores editoriales. Las traducciones proceden del corpus y no han recibido nuevo cotejo filológico ni revisión de una persona especialista. Las pruebas de software no validan el contenido lingüístico ni demuestran eficacia educativa. La próxima revisión sustantiva es cotejar las doce ayudas y sus contextos con una persona competente en náhuatl clásico y probar el recorrido con principiantes.

Las imágenes siguen siendo enlaces externos, con atribución y términos específicos por registro; necesitan conexión y dependen de la disponibilidad del catálogo. No se copian ni se usan para entrenamiento. El cuaderno se conserva en el navegador y origen actual; no se sincroniza entre dispositivos.
