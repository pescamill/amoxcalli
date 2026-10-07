# Validación de la integración · 2026-09-27

## Resultado

- 12 pruebas de corpus y servidor: pasaron. Registro reproducible en `tests-corpus.txt`.
- 13 pruebas existentes de Voces: pasaron nuevamente. Registro en `tests-community.txt`.
- 5 comprobaciones DOM + HTTP de la plataforma unificada: pasaron. Registro en `platform-ui-check.txt`.
- 5 comprobaciones DOM + HTTP de Voces, incluido WAV sintético y retiro: pasaron nuevamente. Registro en `community-ui-check.txt`.
- Sintaxis Python y JavaScript comprobada.
- Los seis archivos de adaptadores `.safetensors` conservan exactamente el SHA-256 del paquete anterior.

## Qué se verificó

Migración sin perder el perfil de Voces; conservación de los 17 IDs de Scriptorium; búsqueda sin acentos conservando la grafía original; acepciones separadas; ausencia explícita de glifo o forma moderna; importación atómica; rechazo de referencias rotas y versiones caducadas; revisión con derechos; identificación de fuente primaria; permisos independientes de consulta y entrenamiento; retiro y eliminación del contenido histórico; rechazo de accesos de otro participante; protección de origen; modelo deshabilitado por defecto; reglas limitadas y formulario JEV sin API.

En integración, un perfil creado desde Voces envió una forma léxica al extractor usando la misma sesión. El aporte quedó pendiente y fuera del corpus consultable; se retiró desde la interfaz. Se comprobó que un texto con etiquetas HTML se muestra como texto y no se ejecuta.

## Inspección visual

Se navegó con Chrome por léxico, acepción «mes» sin glifo, fuentes y extractor. Se inspeccionó el extractor dentro de un marco de prueba de 390 px (375 px de contenido al descontar el scroll): ancho de documento y de contenido desplazable coincidentes, sin desbordamiento horizontal. Este arnés solo existe en el entorno de QA, no se distribuye ni relaja los encabezados de seguridad del producto.

Capturas incluidas: `docs/scriptorium-lexico.jpg` y `docs/scriptorium-mobile.jpg`.

## Límites de las pruebas

No se probó un teléfono físico ni el micrófono real. El marco estrecho verifica distribución, no equivalencia completa con Safari/iOS o Chrome/Android. La integración de audio usa un WAV sintético, no una grabación de un hablante. No se cargaron los pesos ni se volvió a entrenar el modelo durante esta integración; se preservaron intactos. No se publicó una actualización del sitio alojado anterior.

Las pruebas informáticas no acreditan corrección lingüística ni cotejo filológico. La semilla distingue referencias heredadas y fichas secundarias consultadas. La exportación de entrenamiento empieza vacía por falta de permisos/cotejos suficientes en esa semilla; no es un fallo de recolección.

## Reproducir

```bash
python3 -m unittest discover -s tests -p 'test_corpus.py' -v
python3 -m unittest discover -s tests -p 'test_community.py' -v
```

Para las pruebas DOM, instala `jsdom@26.1.0` en un directorio de QA externo (solo desarrollo), configura `NODE_PATH` a su carpeta `node_modules` y ejecuta:

```bash
python3 scripts/test-platform-ui.py
python3 scripts/test-community-ui.py
```

Los scripts crean servidores y bases temporales y los cierran al terminar. No escriben en la base de una instalación real.
