# Voces · colaboración de hablantes

Voces forma parte de Amoxcalli en `/aportar` y la sirve el mismo proceso que el resto de la aplicación (arranque: `make demo` o `bash scripts/amoxcalli.sh serve`); reconocer y traducir usan el archivo completo de 16.111 pares. Las misiones de ejemplo descritas abajo quedan en el almacén (`import-tasks`) y en las pruebas. Operación y revisión: [PLATAFORMA.md](PLATAFORMA.md).

App local para reunir juicios de lectura, traducciones propuestas, grabaciones y revisiones entre participantes. El código usa la licencia MIT del proyecto. No requiere descargar el modelo, instalar PyTorch, pagar una API ni crear una cuenta externa. Esta primera versión sirve para un piloto acompañado; la información lingüística necesita revisión antes de entrenar.

## Abrir la app

Desde la carpeta `nahuatl-local`, con Python 3.11 o 3.12:

```bash
bash scripts/amoxcalli.sh serve
```

Abre **http://127.0.0.1:8766/aportar** en el mismo equipo. En Windows: `py -m nahuatl_local.platform serve`. Voces no tiene servidor propio; `python3 -m nahuatl_local.community` queda para la administración por consola (`queue`, `import-tasks`, `curate`, `export`, `export-observations`).

El servidor guarda los datos en `data/community/voces.sqlite3`. La base, sus archivos auxiliares y las grabaciones no se incorporan al ZIP distribuido. Conserva una copia de seguridad del directorio de datos con el servidor detenido. Una sesión de participante permanece en su navegador; distintos perfiles de navegador representan participantes distintos. Editar un perfil conserva la identidad y no crea una cuenta nueva.

## Misiones disponibles

| Misión | Qué recoge | Cómo se interpreta |
|---|---|---|
| Reconocer | Comprensión completa/parcial/nula o dificultad para leer; impresión sobre variante/clásico; seguridad; explicación opcional | Observación de esa persona y variante; no certificación histórica |
| Escribir o hablar | Propuesta para un estímulo español, texto y/o audio | Traducción pendiente; la variedad del perfil queda registrada en el momento del envío |
| Escuchar | Audio de otra persona de la misma variante, transcripción opcional y juicio de significado | Revisión independiente; puede conservar desacuerdo |
| Revisar | Texto de otra persona de la misma variante, juicio y propuesta opcional | Revisión independiente; nunca aprobación automática por mayoría |

Hay 30 denominaciones de referencia tomadas del [catálogo INALI](https://www.inali.gob.mx/sitios/clin-inali/html/l_nahuatl.html), consultado el 23 de septiembre de 2026. Se puede introducir otra denominación o dejar la variante por identificar. Los códigos `inali-00`, etc., son identificadores internos de esta app, **no códigos ISO**. La autodenominación y la comunidad/región opcional se conservan, junto con la experiencia lingüística e histórica autodeclaradas.

La comparación de revisiones usa la misma etiqueta de variante; dos denominaciones libres diferentes no se fusionan automáticamente. Si distintas etiquetas se refieren a la misma comunidad, el proyecto debe acordar un mapeo explícito antes de agregar datos. Ser hablante de una variedad actual no concede por sí solo una certificación de náhuatl clásico.

El inicio contiene **12 misiones de demostración**: tres palabras aisladas con enlaces al catálogo léxico usado por el proyecto, una frase compuesta sin validar y ocho estímulos originales en español. No es un corpus revisado. No se copiaron grabaciones de personas ni imágenes de códices. Los enlaces de consulta requieren internet si se abren; la app opera sin ellos.

## Voz

El botón graba hasta 60 segundos mediante el micrófono del navegador, permite escuchar y descartar antes de enviar, y apaga las pistas al terminar. Requiere `localhost`/`127.0.0.1` o HTTPS, además del permiso de micrófono del navegador. También se pueden subir archivos propios WebM, Ogg, WAV o M4A de hasta 8 MB.

No hay reconocimiento de voz automático. Otras personas pueden proponer una transcripción; el responsable debe revisarla antes de aprobar un par. El servidor comprueba tamaño y cabecera del contenedor, pero no identifica la lengua, no demuestra que la voz sea de quien la aporta y no mide la duración real de los archivos subidos. Antes de entrenar un modelo de voz hay que comprobar que el archivo decodifica, duración, canales, frecuencia, ruido y alineación con la transcripción.

## Puntos y logros

- 10 puntos por misión enviada, una sola vez por participante y estímulo.
- 5 por revisión de otra persona, una sola vez por aportación; no se permite la autorrevisión.
- 10 adicionales cuando el responsable aprueba una traducción.
- Meta diaria opcional de cinco aportaciones/revisiones (día UTC), sin pérdida de rachas, cronómetro competitivo ni tabla pública de posiciones.

«No sé» obtiene los mismos puntos. Dar permiso de entrenamiento no da puntos extra. Los contadores se calculan a partir de registros vigentes: retirar una aportación elimina sus puntos. Se conservan las diferencias de respuesta y no se premia coincidir con la mayoría. Los perfiles son seudónimos autodeclarados; no se implementó verificación de identidad ni resistencia a crear múltiples perfiles. Por eso los puntos no son una medida de fiabilidad ni deben canjearse por premios en esta versión.

## Consentimiento y retiro

El perfil requiere aceptar la participación como persona adulta. Cada envío distingue permiso de revisión, declaración de autoría y dos opciones de entrenamiento sin marcar: texto/transcripciones y grabación. Los textos y audios enviados pueden ser revisados por el responsable; las traducciones pueden ser revisadas por participantes de la misma variante. No existe una lista pública de voces.

`Mis aportaciones` permite descargar las respuestas como JSON y retirar registros. El retiro elimina el contenido activo, grabación y revisiones asociadas, y limpia el texto de su historial de curación. Se conserva una marca de retiro para evitar repetir la misma misión y para seguimiento. Si se retira una revisión que pudo respaldar una aprobación, la aportación vuelve a pendiente. La eliminación lógica no equivale a borrado forense de discos o copias de seguridad; las exportaciones existentes y los modelos anteriores requieren gestión del responsable.

El permiso de entrenamiento se limita a este proyecto y se exporta como `project_training_only`. **No autoriza publicar automáticamente un corpus abierto** ni asignarle MIT. Antes de redistribuir datos o pesos derivados hay que acordar los permisos con las personas y comunidades involucradas. El código sí es abierto. La interfaz no solicita correo, nombre real, domicilio o geolocalización.

## Añadir material

Cada línea del archivo es un objeto JSON con `id`, `kind` (`recognize` o `translate`), `text` y `source`. Usa identificadores estables, fuente, localizador si existe y una nota sobre el permiso de uso. Los registros de validación o prueba declarados como tales se rechazan. Esta comprobación no descubre todas las copias o paráfrasis de obras reservadas: la revisión del responsable sigue siendo necesaria.

```bash
python3 -m nahuatl_local.community import-tasks templates/community-tasks.jsonl
```

Para traer el corpus del traductor, genera misiones únicamente desde la partición de entrenamiento, conservando ID, obra, página/folio, variante de origen y procedencia. No uses los textos de evaluación como misiones para mejorar ese mismo modelo. La app no descarga ni redistribuye libros automáticamente.

## Revisar y preparar datos para entrenamiento

La revisión final se hace desde la terminal del responsable; no hay un rol de experto que cualquiera pueda activarse en la interfaz. Consultar la cola imprime aportaciones, permisos, fuente y observaciones de otros participantes:

```bash
python3 -m nahuatl_local.community queue
```

Sustituye `ID` por una aportación real y los textos descriptivos por los datos de la revisión. Para una variedad actual:

```bash
python3 -m nahuatl_local.community curate ID \
  --decision accepted --language modern \
  --reviewer 'Identificador del revisor autorizado' \
  --evidence 'Qué se comprobó y cómo se resolvieron las diferencias'
```

Si la propuesta solo tiene audio, añade `--text 'Transcripción revisada'`. El responsable debe tener autorización para sus correcciones y para usar cualquier texto de revisores que incorpore. La app no convierte una sugerencia de un tercero en autorización de uso.

Para clasificar una propuesta como náhuatl clásico, además de revisión especializada se exige dejar constancia de fuente histórica y localizador:

```bash
python3 -m nahuatl_local.community curate ID \
  --decision accepted --language nci \
  --reviewer 'Identificador del revisor especializado' \
  --evidence 'Justificación de la construcción y de su fidelidad' \
  --source-url 'https://sitio-de-la-fuente.example/obra' \
  --locator 'Edición, página o folio consultado'
```

La URL del ejemplo es un marcador, no una fuente real. Introducir una URL no verifica que la revisión sea cierta: el registro lleva `organizer_declared`. Las misiones de reconocimiento no pueden aprobarse como pares de traducción.

```bash
python3 -m nahuatl_local.community export --language modern --output data/community/modernos-v1.jsonl --include-audio
python3 -m nahuatl_local.community export --language nci --output data/community/clasico-v1.jsonl
python3 -m nahuatl_local.community export-observations --output data/community/observaciones-v1.jsonl
```

Las exportaciones de traducción incluyen únicamente pares aprobados y con permiso de texto; los audios requieren además permiso de voz. Si no existen registros elegibles, el comando lo informa sin crear un conjunto vacío. No sobrescribe exportaciones. Genera un manifiesto con fecha, IDs y hash. La variante actual se mantiene separada de `nci`; las observaciones se exportan en otro archivo, con `expert_verified=false`. Las revisiones entre participantes solo se exportan cuando tanto el autor original como el revisor permiten el uso de texto para entrenamiento.

El JSONL está **preparado para organizar un conjunto de datos**, con campos `es`, `nah`, variante, grupos de hablante y estímulo, permisos y revisión. `split` comienza como `unassigned`. No modifica automáticamente `data/prepared` ni inicia entrenamiento. Antes de incorporarlo: agrupar variantes ortográficas y estímulos equivalentes; separar por hablante y familia de estímulo para evitar fuga; auditar solapamientos con las obras reservadas y acordar derechos. El entrenador clásico actual no admite introducir indiscriminadamente pares de variedades actuales. El importador CSV anterior tampoco admite `project_training_only` como una licencia de redistribución.

## Invitar participantes

Para probar en el mismo equipo, usa perfiles de navegador separados y datos de demostración. Para colaborar desde teléfonos o a distancia, sirve la app detrás de un proxy HTTPS administrado por el proyecto y establece su origen exacto:

```bash
bash scripts/amoxcalli.sh serve --host 127.0.0.1 --port 8766 --public-origin https://tu-dominio.example
```

El proxy debe conservar el encabezado `Host` y terminar TLS. No se despliega ni se contrata hosting con este comando. El código no usa API externa. Una convocatoria pública requiere añadir gestión de invitaciones, recuperación de sesiones, moderación, cuotas de almacenamiento y operación del servidor. El piloto usa sesiones aleatorias con cookie HttpOnly/SameSite, valida origen/Host de las escrituras, limita cargas y mantiene las decisiones de curación fuera de HTTP. `http.server` es un servidor de piloto; no se presenta como infraestructura pública endurecida.

## Verificar

```bash
python3 -m unittest discover -s tests -p test_community.py -v
```

Los casos cubren consentimiento, reintentos simultáneos, acceso al audio, separación de variantes, autorrevisión, exportación, retiro y origen de las solicitudes. Son pruebas del funcionamiento del sistema; no acreditan competencia lingüística de aportantes o traducciones.
