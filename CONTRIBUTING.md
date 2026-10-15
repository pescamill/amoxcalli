# Mejorar Amoxcalli

Empieza por una duda o una dificultad observable: un pasaje confuso, un vínculo sin respaldo, una traducción por cotejar o una acción difícil de encontrar. La [dirección del proyecto](docs/PROPOSITO.md) prioriza una lectura revisada y probada antes de ampliar el inventario. Puedes aportar sin programar y sin permitir entrenamiento.

## Una corrección pequeña y útil

Registra estos cinco datos en una incidencia del repositorio, una propuesta en la instalación o un archivo Markdown para el responsable:

1. **Dónde:** ID de pasaje, acepción o lectura y su versión. Copia la escritura original.
2. **Problema:** qué observaste y por qué puede confundir; distingue un error de una interpretación alternativa.
3. **Evidencia:** obra, edición, página/folio/entrada y enlace cuando exista. Si es testimonio actual, indica la variedad y el contexto con permiso; no publiques datos privados.
4. **Propuesta:** corrección o pregunta que debería revisarse; admite «no sé» y conserva desacuerdos.
5. **Alcance y permisos:** qué puedes afirmar y qué está pendiente; quién puede revisar o publicar la aportación.

En la aplicación, Fuente, contexto y estado de revisión → Aportar un cotejo abre el pasaje con sus datos. Se necesita un perfil local de Voces para guardarlo. Las propuestas quedan pendientes y no reemplazan automáticamente el corpus. Si no deseas un perfil, usa el formato anterior como documento y entrégalo al responsable por un canal acordado. Los archivos descargados desde Proyecto y colaboración describen este proceso.

Ser hablante de una variedad actual y revisar un texto clásico son tareas distintas. Los aportantes deben poder decidir cómo se identifica su trabajo, qué se conserva y cuáles son sus usos. No copies voces, nombres privados ni materiales comunitarios a una incidencia pública. El permiso para entrenar es opcional y no autoriza por sí solo redistribuir datos.

## Añadir contenido por lotes

Usa el [pipeline editorial](docs/EDITORIAL_PIPELINE.md) para extracción/concordancias y el [ensamblador de lecturas](docs/LECTURAS_PIPELINE.md) para recetas explícitas. Conserva IDs, originales, hashes, localizadores, épocas y variantes; separa la paleografía de una normalización de catálogo. Documenta respaldo y resultado de la verificación. No reutilices un lote cuyo hash base haya cambiado.

Una coincidencia de texto es un candidato, no una equivalencia léxica. Una imagen relacionada puede ser útil si se explica su alcance con evidencia; dejar una imagen pendiente es preferible a inventar una conexión. Las generaciones del modelo no se usan como traducciones correctas ni fuentes.

La revisión registra responsable autorizado, fecha, evidencia, decisión y límites. No se marca «revisado» por haber pasado un script. Si falta evidencia, conserva el pendiente o excluye la afirmación del piloto.

## Cambiar la aplicación

Haz cambios acotados, conserva el almacenamiento del cuaderno y los permisos existentes, y explica el problema que resuelves. Verifica el recorrido afectado con teclado y tamaño de teléfono cuando cambie su interfaz. No amplíes la recogida de datos para medir uso sin un acuerdo explícito.

```bash
bash scripts/plataforma.sh
python3 -m unittest discover -s tests
npm ci --ignore-scripts
npm run test:ui
npm run test:offline
```

Algunas pruebas Python necesitan dependencias de entrenamiento y fuentes cacheadas; consulta las guías antes de concluir que una instalación mínima falla. Usa el entorno `.venv` si está preparado. Las pruebas de interfaz arrancan una base temporal, sin modificar las aportaciones de tu instalación. Para un cambio concreto, ejecuta primero las pruebas relevantes; no hace falta entrenar ni descargar pesos para mejorar la lectura.

Describe en la propuesta el comportamiento resultante, la verificación realizada y cualquier duda pendiente. Actualiza la guía correspondiente y registra la entrega en `docs/PROGRESO_INTERNO.md`. Los informes históricos se conservan; las prioridades actuales viven en `docs/PROPOSITO.md`.

## Licencias y acceso

El código y los documentos originales son MIT. Los textos, imágenes y otros materiales tienen condiciones propias; consulta [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md). No adjuntes bases de participantes, grabaciones o exportaciones privadas a Git. La licencia abierta y la visibilidad pública del repositorio son decisiones diferentes; la publicación de una colección exige revisar sus derechos.
