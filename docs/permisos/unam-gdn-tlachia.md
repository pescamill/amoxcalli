# Borrador · Solicitud de permiso al Gran Diccionario Náhuatl y a Tlachia (UNAM)

> **Borrador sin enviar** (15 de octubre de 2026). Completar los campos entre corchetes, revisar las cifras con `make reports` y confirmar el destinatario antes de enviarlo. No se ha contactado a nadie.

**Para:** Coordinación del Gran Diccionario Náhuatl y del proyecto Tlachia · Instituto de Investigaciones Bibliográficas, UNAM
[nombre de la persona responsable · correo institucional publicado en la página de créditos]

**De:** [nombre], responsable de Amoxcalli · [correo] · [institución o afiliación, si la hay]

**Asunto:** Solicitud de permiso para enlazar e incorporar entradas del GDN y fichas de Tlachia, con atribución, en una plataforma educativa de náhuatl clásico

---

Estimada coordinación:

Le escribo para presentarle **Amoxcalli**, una plataforma local y gratuita para aprender a leer náhuatl clásico, y para pedirle permiso explícito sobre el uso que hacemos —y quisiéramos hacer— del Gran Diccionario Náhuatl y de Tlachia.

**El proyecto.** Amoxcalli reúne lecturas guiadas de fragmentos clásicos, un diccionario con fuentes, el archivo bilingüe Axolotl (16.111 pasajes) y un analizador morfológico transparente. Funciona en la computadora de quien lo usa, sin publicidad ni cuentas comerciales. Su código es abierto (MIT); los textos y las imágenes de terceros conservan sus condiciones y no se relicencian. Cada ficha muestra su fuente, su localizador y su estado de revisión, y distingue la transcripción automática de la revisión de una persona especialista.

**Lo que ya hacemos, para su conocimiento.** Antes de pedir este permiso incorporamos, de buena fe y con atribución, dos conjuntos limitados que les pedimos revisar:

- **GDN:** 549 entradas de Molina (1571, parte 2) extraídas automáticamente de las páginas de consulta del GDN, con paleografía y traducción literales, enlace a `/contexto/{id}` y hash de la página consultada. No se descargó el diccionario completo; las páginas se guardan en una caché local que no se distribuye. Ninguna entrada se usa para entrenar modelos.
- **Tlachia:** un índice de 13 láminas (Telleriano-Remensis, Calpan y Matrícula de Huexotzinco · Tianquiztenco) con lecturas, elementos y valores tal como los registra el catálogo, atribuidos a sus investigadoras e investigadores. Las imágenes se cargan desde su sitio; no se copian ni redistribuyen.

Si alguno de estos usos no les parece adecuado, lo retiraremos de inmediato y se lo confirmaremos por escrito.

**Lo que solicitamos.** Les pedimos autorización, en el grado que ustedes consideren, para:

1. **Consulta y enlace:** mostrar enlaces a las entradas del GDN y a las láminas de Tlachia desde las fichas correspondientes.
2. **Incorporación con atribución:** conservar e incorporar más entradas del GDN (lema, paleografía, traducción histórica y fuente) y más fichas de Tlachia (lecturas, elementos y valores), siempre con el crédito que ustedes indiquen, enlace a la ficha original y la marca «extracción automática» hasta su revisión.
3. **Imágenes de Tlachia:** seguir mostrándolas cargadas desde su sitio y, si lo permiten, guardar una copia local solo para uso sin conexión dentro de la aplicación (no para redistribuirla).

**Lo que no pedimos.** El entrenamiento de modelos de lenguaje queda **excluido**: no usaremos estos datos para entrenar ni ajustar modelos salvo que ustedes lo autoricen expresamente y por escrito. Tampoco pedimos permiso de uso comercial ni de redistribución fuera de la plataforma.

**Lo que ofrecemos.**

- Atribución visible en cada ficha, con la forma de cita que nos indiquen, y enlace a su sitio en lugar de sustituirlo.
- Un registro por entrada de procedencia, fecha de consulta, hash y estado de revisión, que podemos compartirles para que verifiquen lo incorporado.
- Lotes acotados con caché local: sin rastreo masivo ni carga sobre sus servidores.
- Avisarles de las erratas o inconsistencias que encontremos al cotejar sus fichas.
- Retirar cualquier contenido a petición suya, en un plazo de [7] días.
- Compartir con su equipo las herramientas abiertas del proyecto (analizador, índice de términos, lecturas) por si les resultan útiles.

Con gusto les presentamos la plataforma en una sesión breve o les enviamos una copia del índice para su revisión. Agradezco de antemano su tiempo y el trabajo de muchos años que hace posibles el GDN y Tlachia.

Atentamente,

[nombre]
[correo · enlace al repositorio, si se publica]

---

### Para quien envía (no forma parte de la carta)

- Cifras al 15 de octubre de 2026: 549 entradas GDN/Molina (`corpus/gdn-lexicon-v6.json`, `corpus/editorial-batch-007-v9.json`), índice pictográfico en `corpus/pictography/catalog.json`. Actualizarlas si cambian.
- Registrar la respuesta en `docs/FUENTES.md` y, si se concede algo, el alcance exacto (consulta, incorporación, imágenes, entrenamiento) en `rights` de las fichas afectadas.
