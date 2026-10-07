# Validación de Voces

Se verificó la app con información sintética, sin aportaciones de hablantes reales ni incorporación de datos al entrenamiento. El modelo entregado conserva sus pesos anteriores.

- **13 pruebas de almacenamiento/HTTP aprobadas**, registradas en `tests-community.txt`: permisos, intentos simultáneos, autorrevisión, acceso a audio, variantes, evaluación reservada, retiro, observaciones y exportación.
- **Integración DOM + HTTP aprobada**, registrada en `community-ui-check.txt`: perfil, impresión de lectura, puntos sin permiso de entrenamiento, carga de un WAV sintético por la lógica de la interfaz, reproducción disponible por sesión, presentación segura de texto y retiro. Usa jsdom; no equivale a una prueba de micrófono o reproducción acústica en un navegador real.
- **Navegador de escritorio:** se inspeccionaron el inicio, selección de variante y permisos, el envío de una impresión de lectura y el estado de éxito con 10 puntos. La captura `docs/voces-preview.jpg` muestra la interfaz real con un perfil de prueba. Se inspeccionó también la misión de escritura/voz y su indicación de que el micrófono necesita un contexto compatible. La carga desde el selector de archivos del navegador no se dio por verificada; la comprobación completa de carga/retiro corresponde a DOM + HTTP.
- **Sin prueba física de micrófono ni de teléfono.** El código utiliza MediaRecorder, permiso de micrófono y límite de 60 s. Debe comprobarse en los dispositivos del piloto, especialmente Safari/iOS y HTTPS para participación remota. La interfaz tiene reglas adaptables, pero no se atribuye una validación visual móvil que no se realizó.

La suite del modelo (informe previo de 16 pruebas) no se volvió a ejecutar: no se cambiaron el entrenador ni sus pesos y esta app no importa esas dependencias. Las pruebas nuevas no acreditan competencia lingüística, autenticidad de identidad o validez de las revisiones históricas declaradas.

## Reproducir

```bash
python3 -m unittest discover -s tests -p test_community.py -v
```

La prueba DOM adicional usa una dependencia solo de desarrollo. Instálala en un directorio de pruebas separado:

```bash
npm install --prefix /tmp/voces-ui-tests jsdom@26.1.0 --no-audit --no-fund
NODE_PATH=/tmp/voces-ui-tests/node_modules python3 scripts/test-community-ui.py
```

El lanzador abre un servidor en un puerto libre con base temporal, ejecuta la prueba y lo cierra. No requiere instalar dependencias Node para usar Voces. La base temporal y su WAV sintético no se distribuyen como datos lingüísticos.
