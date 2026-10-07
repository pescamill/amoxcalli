# Scriptorium en móvil y escritorio

Una webapp reúne aprendizaje mediante ejemplos, diccionario glífico, laboratorio del LLM y colaboración con texto y voz. La consulta funciona sin instalar el modelo; el arranque completo prepara también la generación local, sin claves ni API externa. Python 3.11 o 3.12 y SQLite guardan los datos en tu equipo; el navegador presenta la interfaz adaptable.

## Arranque en tu equipo

Descomprime el paquete y, dentro de `nahuatl-local`, ejecuta:

```bash
bash scripts/plataforma.sh
```

En Windows, desde PowerShell, usa `py -m nahuatl_local.platform serve`.

Abre http://127.0.0.1:8766. Consulta «agua», abre su referencia glífica y sigue el enlace a su fuente. En «Voces · texto y voz», crea un perfil con tu variante y completa una misión. En «Aportar», registra una forma, texto o referencia glífica con su fuente y localizador. Los envíos quedan pendientes de revisión y aparecen en tus aportaciones.

La revisión editorial y la importación por lotes se administran desde terminal; los comandos están en [PLATAFORMA.md](PLATAFORMA.md). No existe todavía un panel de administración con roles recuperables.

## Teléfono en la misma red

Sustituye la dirección del ejemplo por la IP local del equipo servidor:

```bash
bash scripts/plataforma.sh --host 192.168.1.25 --port 8766
```

Abre `http://192.168.1.25:8766` en el teléfono conectado al mismo Wi-Fi. Autoriza el puerto en el cortafuegos local si es necesario. Puedes buscar, escribir y cargar un audio ya grabado. Usa la IP concreta en `--host`: el servidor comprueba el encabezado Host.

## Instalación y micrófono mediante HTTPS

Para instalar en el teléfono y capturar el micrófono, sirve la app con HTTPS confiable para ese dispositivo. En escritorio, `localhost` también permite estas funciones. El botón «Instalar app» ofrece el diálogo del navegador cuando está disponible; en iPhone/iPad, usa Compartir → Añadir a pantalla de inicio. La disponibilidad depende del navegador.

Si administras un dominio y un proxy HTTPS, por ejemplo Caddy, esta es la configuración de referencia (sustituye el dominio):

```caddyfile
nahuatl.example.org {
    reverse_proxy 127.0.0.1:8766
}
```

Arranca la app en el mismo equipo del proxy:

```bash
bash scripts/plataforma.sh --public-origin https://nahuatl.example.org
```

El proxy debe conservar el Host y servir un certificado válido. Esta configuración requiere que tú dispongas del dominio, red y certificado; el paquete no crea ni publica un servidor. Para un piloto privado, limita su acceso al grupo participante. El piloto conserva sesiones locales, pero aún no incorpora recuperación de cuentas ni cuotas de almacenamiento para un servicio público.

## Conexión y datos

El corpus, perfiles y aportaciones viven en `data/community/`. La instalación del navegador es un acceso a ese servidor: el equipo debe permanecer encendido. No necesita internet para consultar los datos locales; abrir catálogos externos sí lo requiere.

Si se pierde la conexión, una pantalla explica cómo volver a conectar. No hay cola de envíos ni consulta del corpus sin conexión al servidor. Solo se cachea esa pantalla: no se almacenan perfiles, audio ni copias del corpus en la caché del navegador. Un envío cuenta como guardado cuando aparece su confirmación y figura entre las aportaciones.

Para actualizar: detén el servidor, respalda `data/community/`, reemplaza el código conservando esa carpeta y vuelve a arrancar. La actualización glífica es automática, no duplica fichas ni sustituye ediciones locales. No hace falta reiniciar ni entrenar el modelo.

## Alcance comprobado

Se comprueban mediante pruebas locales la consulta, los enlaces glíficos, los envíos escritos, el retiro, la sesión compartida, las rutas del manifiesto y las exportaciones. La instalación real y el permiso de micrófono deben probarse también en los teléfonos y navegadores de tu grupo.

Referencia técnica: [requisitos de instalación de una PWA, MDN](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable).

## Consulta completa y dos espacios

La pantalla inicial ofrece 6 lecturas con 24 ejemplos de 6 obras, ayuda contextual y ejercicios. Leer, Diccionario y Mis palabras completan el recorrido; el diccionario tiene 575 acepciones / entradas (26 curadas y 549 transcripciones automáticas de Molina/GDN), con 139 entradas vinculadas a imágenes de fuente. La página inicial conserva las 24 palabras representativas; las otras entradas siguen el alfabeto náhuatl, 48 por página. Los filtros muestran coincidencias alfabéticas. Las referencias de contexto explican que no escriben la palabra. El script local `nahuatl_local.glyph_linker` genera enlaces e informe sin red ni modelo; 436 entradas siguen pendientes de evidencia. El archivo completo consulta 16.111 pares de Axolotl (33 obras identificadas y un registro sin título), con filtros por variedad y obra y resultados paginados. Las fichas editoriales no delimitan la consulta general. «Aportar cotejo» precarga un pasaje y conserva su variedad original aunque el perfil de quien aporta use otra.

En Aportar, la misión inicial es escribir/hablar. Reconocer, escuchar y revisar están en la barra de tareas. La pantalla conserva las funciones de consentimiento, retirada y participación. Aprender y Aportar son espacios de trabajo, no cuentas con privilegios nuevos; la aceptación editorial sigue por terminal.

El modelo se detecta al arrancar y se carga en memoria al generar. «Opciones» muestra si faltan la base, el adaptador o dependencias. El formato con pasajes dentro de la instrucción queda en los controles avanzados, desactivado por defecto porque el adaptador no se entrenó con ese formato. Los pasajes relacionados se muestran de todas formas para consulta.


## Laboratorio y progreso

Laboratorio está en la navegación principal con tres pestañas: Probar, Datos de entrenamiento y Modelo y progreso. Datos presenta los 650 pares recorridos por el adaptador, los conjuntos preparados y formularios para proponer pares manualmente o por CSV. En Probar se elige entre búsqueda, borrador del LLM y reglas; el experimento de contexto explica y permite ver los ejemplos que recibe el modelo. Para instalar el modelo en un equipo nuevo, usa `bash scripts/iniciar.sh`; no hace falta para leer los informes. Consulta [LABORATORIO.md](LABORATORIO.md) y [PROGRESO_INTERNO.md](PROGRESO_INTERNO.md). El cuaderno educativo usa almacenamiento local del navegador; permanece separado de perfiles y aportaciones del servidor.
