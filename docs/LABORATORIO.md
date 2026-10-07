# Laboratorio del LLM

La navegación principal abre **Laboratorio** en `http://127.0.0.1:8766/#modelos`. Tiene tres pestañas: [Probar](http://127.0.0.1:8766/#modelos/probar), [Datos de entrenamiento](http://127.0.0.1:8766/#modelos/datos) y [Modelo y progreso](http://127.0.0.1:8766/#modelos/progreso).

## Probar: elegir el método

La opción inicial **Buscar ejemplos con fuente** consulta pasajes existentes en español y náhuatl, sin ejecutar el LLM. **Generar un borrador con el LLM** usa Qwen3-0.6B y el adaptador LoRA local, todavía poco fiable; muestra método, tiempo y límites de la salida. **Consultar reglas léxicas limitadas** conserva los patrones locales acotados. El resultado del generador se exporta como ficha para revisión, nunca como respuesta correcta.

La antigua opción «Añadir pasajes» se presenta dentro de **Experimento con ejemplos de referencia**: el buscador elige hasta dos pares relacionados y los copia delante de la frase en el mensaje enviado al modelo. **Ver qué ejemplos recibirá** permite inspeccionarlos antes de generar. Esto es RAG: cambia el contexto de esa petición, no los pesos. Nuestro adaptador se entrenó sin ese formato, por lo que no se promete una mejora. La evidencia aparece separada del borrador.

El modelo recibe texto, no imágenes glíficas. Las lecturas guiadas conservan ejemplos del corpus y claves editoriales; guardar palabras, aportar pares y abrir el laboratorio no inicia entrenamiento.

## Datos: español y náhuatl lado a lado

El visor permite buscar en ambos idiomas, filtrar obra, paginar 20 pares y descargar la página con procedencia. Distingue:

| Conjunto | Pares | Qué significa |
|---|---:|---|
| Recorridos por el adaptador | 650 | 400 del piloto + 250 de continuación, identificados mediante orden y cursor del checkpoint |
| Preparación histórica de entrenamiento | 2.248 | Incluye 1.759 pares admisibles a 192 tokens; no todos fueron recorridos |
| Entrenamiento actual | 2.161 | Preparación `nah-ortho-1`; los pesos actuales no se entrenaron con ella |
| Validación actual reservada | 2.049 | Evaluación, excluida de nuevas aportaciones al entrenamiento |
| Prueba actual reservada | 1.252 | Evaluación reservada |

Los JSONL históricos se reconstruyeron desde el CSV original y sus tres SHA256 coinciden exactamente con `outputs/continued-unseen/automation.json`. La referencia y los IDs recorridos están en `data/training-reference/continued-unseen/`; se verifican al arrancar. El script de reconstrucción no modifica el corpus preparado ni los pesos:

```bash
.venv/bin/python scripts/reconstruct-training-reference.py --output /tmp/referencia-historica-nueva
```

Necesita el tokenizador y checkpoint locales para recuperar el orden. El visor usa la referencia incluida y no requiere PyTorch ni cargar pesos. Las alineaciones originales siguen pendientes de revisión filológica propia; que un par se haya usado para entrenar no certifica su traducción.

## Añadir pares

Con un perfil de **Aportar** en la misma sesión puedes guardar un par español/náhuatl clásico o importar CSV UTF-8 usando la plantilla descargable. Cada par conserva texto, obra, localizador, fuente y licencia/permiso. El CSV admite comas y saltos de línea entre comillas, hasta 200 filas y 500 KB. Los errores se indican por fila. Cada envío requiere permiso para compartir, revisión y eventual entrenamiento.

Las propuestas se guardan privadas en SQLite. Puedes ver y retirar las tuyas. No se publican ni modifican los conjuntos de entrenamiento automáticamente. Se bloquean duplicados y obras reservadas. Una persona responsable debe revisar traducción y permisos; la aceptación sigue en terminal, con motivo y revisor:

```bash
.venv/bin/python -m nahuatl_local.training_data review ID_DE_PROPUESTA \
  --reviewer 'Nombre del responsable' --reason 'Cotejo y permisos documentados' \
  --rights-checked --linguistic-checked
.venv/bin/python -m nahuatl_local.training_data export --output data/pares-revisados-nuevos.csv
.venv/bin/python -m nahuatl_local.curate data/pares-revisados-nuevos.csv \
  --base data/prepared --output data/curated-nuevo
```

Usa rutas nuevas: los comandos rechazan sobrescritura. El navegador descarga solo tus pares aceptados; el responsable puede exportar todos los aceptados desde terminal. `curate` conserva validación y prueba byte por byte y escribe otra preparación. Entrenar es un paso posterior explícito; ver [MEJORAR.md](MEJORAR.md).

## Modelo y progreso: resultados y procedencia

`GET /api/laboratory` resume informes sin cargar los pesos. Muestra disponibilidad detectada al arrancar, adaptador de referencia/seleccionado, corrida, curva, métricas y hashes. No es un monitor de procesos ni un porcentaje de competencia lingüística.

La referencia es `outputs/continued-unseen/run/best`: 400 pasos heredados y 250 adicionales. La curva de continuación contiene 0/100/200/250; NLL 3,5783 → 3,5302 sobre 128 ejemplos. La comparación de generación usa 12 frases fijas de validación: chrF++ 22,58 → 27,96 y repetición 0 → 0,028. Se comprueban IDs, hash, split, firma y formato antes de marcar una comparación como controlada. La salida registrada «La casa y la flor.» → `Yn otlacuia yn otlacuia.` muestra un fallo real, sin simular una generación nueva.

Los hashes actuales difieren de aquella corrida: esas métricas no evalúan la preparación actual. La recuperación actual usa 100 frases, chrF++ 16,0123, sin LLM; muestras y preparaciones distintas impiden comparación directa. Los informes y resumen de visita son descargables mediante una lista cerrada, sin exponer perfiles ni checkpoints binarios.

No hubo nuevo entrenamiento con estos cambios. Para mejorar el LLM hace falta revisar ejemplos y comparar recuperación, base y adaptador sobre la misma validación actual antes de otra corrida. La ampliación del diccionario conserva `rights.training=false` y no alimenta los pesos.
