# Amoxcalli en móvil y escritorio

Instalación, acceso desde el teléfono, HTTPS y comportamiento sin conexión. Qué ofrece la aplicación: [README](../README.md); operación (revisión, importación, exportación): [PLATAFORMA.md](PLATAFORMA.md). Python 3.11+ y SQLite guardan los datos en tu equipo; el navegador presenta la interfaz adaptable.

## Arranque en tu equipo

Desde la carpeta del repositorio, ejecuta `make demo` (prepara los análisis derivados y arranca) o directamente:

```bash
bash scripts/amoxcalli.sh serve
```

En Windows, desde PowerShell, usa `py -m nahuatl_local.platform serve`. Opciones: [README](../README.md#probarlo).

Abre http://127.0.0.1:8766. Consulta «agua», abre su referencia glífica y sigue el enlace a su fuente. En «Voces · texto y voz», crea un perfil con tu variante y completa una misión. En «Aportar», registra una forma, texto o referencia glífica con su fuente y localizador. Los envíos quedan pendientes de revisión y aparecen en tus aportaciones.

La revisión editorial y la importación por lotes se administran desde terminal; los comandos están en [PLATAFORMA.md](PLATAFORMA.md). No existe todavía un panel de administración con roles recuperables.

## Teléfono en la misma red

Sustituye la dirección del ejemplo por la IP local del equipo servidor:

```bash
bash scripts/amoxcalli.sh serve --host 192.168.1.25 --port 8766
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
bash scripts/amoxcalli.sh serve --public-origin https://nahuatl.example.org
```

El proxy debe conservar el Host y servir un certificado válido. Esta configuración requiere que tú dispongas del dominio, red y certificado; el paquete no crea ni publica un servidor. Para un piloto privado, limita su acceso al grupo participante. El piloto conserva sesiones locales, pero aún no incorpora recuperación de cuentas ni cuotas de almacenamiento para un servicio público.

## Conexión y datos

El corpus, perfiles y aportaciones viven en `data/community/`. La instalación del navegador es un acceso a ese servidor: el equipo debe permanecer encendido. No necesita internet para consultar los datos locales; abrir catálogos externos sí lo requiere.

Si se pierde la conexión, una pantalla explica cómo volver a conectar. No hay cola de envíos ni consulta del corpus sin conexión al servidor. Solo se cachea esa pantalla: no se almacenan perfiles, audio ni copias del corpus en la caché del navegador. Un envío cuenta como guardado cuando aparece su confirmación y figura entre las aportaciones.

Para actualizar: detén el servidor, respalda `data/community/`, reemplaza el código conservando esa carpeta y vuelve a arrancar. La actualización glífica es automática, no duplica fichas ni sustituye ediciones locales. No hace falta reiniciar ni entrenar el modelo.

## Alcance comprobado

Desde Leer, **Preparar ficha para taller** selecciona una lectura publicada. Permite incluir u ocultar traducciones y claves en la vista imprimible. **Imprimir / guardar PDF** abre el diálogo del navegador; no genera un PDF en el servidor. El JSON descargable siempre contiene las claves y el contenido público con sus versiones, hashes y procedencia; no incluye el cuaderno ni el perfil. Las notas se escriben en papel. La ficha conserva las condiciones de los pasajes y no concede permisos de redistribución. La impresión es textual, sin depender del LLM ni de imágenes externas.

Se comprueban mediante pruebas locales la consulta, los enlaces glíficos, los envíos escritos, el retiro, la sesión compartida, las rutas del manifiesto y las exportaciones. La instalación real y el permiso de micrófono deben probarse también en los teléfonos y navegadores de tu grupo.

Referencia técnica: [requisitos de instalación de una PWA, MDN](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable).
