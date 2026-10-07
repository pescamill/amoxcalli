# Datos bilingües, laboratorio y diccionario · 29 de septiembre de 2026

Se simplificó el laboratorio para distinguir búsqueda de ejemplos, generación experimental y consulta de reglas. El modelo continúa produciendo resultados poco fiables; no se ejecutó entrenamiento ni se cambiaron pesos durante esta entrega.

## Entrega

- Tres rutas: `#modelos/probar`, `#modelos/datos`, `#modelos/progreso`. Probar abre en búsqueda con fuente. El contexto RAG tiene explicación y vista previa de hasta dos pares; no se confunde con añadir datos al entrenamiento.
- Visor español/náhuatl, búsquedas, filtro por obra, 20 pares por página y descarga de página. Default: 650 pares recorridos por los pesos, no los 2.248 preparados. Separación explícita respecto de los 2.161 actuales y conjuntos reservados.
- Nuevos pares manuales/CSV quedan privados y pendientes. Perfil y permisos necesarios; bloqueos de duplicados y obras reservadas. Revisión por terminal y exportación de aceptados antes de `curate` hacia otra preparación; validación/prueba se conservan.
- Extracción automática de GDN/Molina: 499 entradas, 998 entidades nuevas, cero llamadas al LLM. Se mantiene grafía paleográfica y español histórico; grafía normalizada separada. Cada ficha tiene ID, enlace, origen y hash de página. No se añaden asociaciones glíficas automáticas.
- Diccionario: 523 acepciones / entradas, 526 formas, 22 referencias glíficas y 21 imágenes documentales existentes. Paginación de 48 fichas y filtro de origen. Los 24 sentidos curados aparecen primero.

## Procedencia y conservación

Los JSONL históricos se reconstruyeron desde el CSV original. Coinciden exactamente con los tres SHA256 de `outputs/continued-unseen/automation.json` (2.248 / 2.066 / 1.313 filas). Orden y cursor del checkpoint recuperan 650 pares recorridos, de 1.759 admisibles a 192 tokens: 400 del piloto + 250 de continuación. La referencia incluye manifest, hashes e IDs. El script reproducible trabaja en directorios nuevos, con tokenizador local y lectura segura del checkpoint; no actualiza pesos ni corpus preparado.

La migración v6 conserva íntegros los 96 registros previos (payload, versiones, origen y fechas), comparados con `data/backups/voces-before-gdn-v6.sqlite3`. Perfiles y aportaciones coinciden con el respaldo. La [comprobación de conservación](data-preservation-v6.json) registra estos resultados sin incluir datos personales. El CSV original mantiene SHA256 `ed8e85f560e78c43385f91ac99d08dee071183749bc1f1aa1b88f1b3a2530878`. El paquete excluye datos privados y caché; solo incluye la referencia histórica dentro de `data/`.

La extracción consultó 1.400 registros de 14 páginas y excluyó 494 compuestos/generados, 373 con prefijos o puntuación, 33 remisiones y una forma curada. [Informe del lote](dictionary-import-v6.json). Se reprodujo byte por byte desde caché, sin red ni LLM. No es una extracción completa del diccionario. Fuente: [GDN, IIB–UNAM](https://gdn.iib.unam.mx/), colección Molina 2 (1571), ya registrada en el proyecto.

## Verificación y límites

149 pruebas: OK, con un fallo esperado de una regla ortográfica deshabilitada. [Salida completa](tests-datos-diccionario-2026-09-29.txt). Prueba DOM del recorrido educativo, diccionario, tres pestañas del laboratorio, propuestas privadas y retiro en base temporal, exportación/CSV: [salida](platform-ui-datos-diccionario-2026-09-29.txt). Se revisó en navegador real el visor, paginación, contexto y procedencia de una entrada automática, además del diseño móvil sin desbordamiento horizontal.

Las entradas automáticas necesitan cotejo y revisión especializada. Su permiso de entrenamiento sigue desactivado. Los pares de Axolotl conservan las limitaciones de la alineación de origen. El próximo paso para mejorar el LLM es revisar una muestra con referencias y permisos y comparar recuperación, base y adaptador sobre la misma validación actual, antes de elegir otra corrida. La UI no convierte las generaciones actuales en respuestas fiables.
