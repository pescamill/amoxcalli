> Estado al 29 de septiembre de 2026: la preparación actual tiene hashes distintos de los usados en las corridas entregadas. No reanudar `outputs/continued-unseen` con estos archivos ni heredar su cursor. Crear una ejecución nueva y evaluar en la preparación actual; consultar [MEJORAR.md](MEJORAR.md) y [LABORATORIO.md](LABORATORIO.md). Las cifras de 1.759 pares y 5.277 pasos siguientes describen la corrida histórica.

# Entrenamiento automático local

Esta versión automatiza el trabajo con los datos existentes. No requiere revisión humana para ejecutar ni una API. La revisión especializada puede venir después; los resultados siguen siendo experimentales.

## Un comando

Python 3.11 o 3.12, macOS o Linux. Extrae el ZIP, entra en `nahuatl-local` y ejecuta:

```bash
bash scripts/autotrain.sh --budget-minutes 60
```

Si `python3` apunta a otra versión, antepone `NAHUATL_PYTHON=python3.12` al comando (con Python 3.12 ya instalado).

La primera vez crea `.venv`, instala las versiones declaradas, descarga la base y el corpus fijados, prepara los datos y arranca. En Linux instala PyTorch CPU; en macOS usa la distribución estándar y elige MPS si está disponible. Solo CPU ha sido probada aquí. La base descarga unos 1,50 GB, además de las dependencias. Hace falta conexión para estas descargas iniciales; entrenamiento e inferencia son locales.

Con el entorno ya instalado y los datos preparados, la ruta totalmente offline es:

```bash
.venv/bin/python -m nahuatl_local.autotrain --budget-minutes 60
```

Se crea `outputs/local-training`. Al iniciar una ejecución nueva, prefiere la continuación corregida de `outputs/continued-unseen/run/best` si supera el filtro de generación en validación y coincide con su checkpoint `last`; después considera la ejecución automática anterior bajo el mismo criterio y, si no, empieza desde el piloto de 400 pasos. Conserva el adaptador y el cursor de entrenamiento, e inicia un optimizador nuevo para la configuración del equipo. En posteriores invocaciones **el mismo comando reanuda pesos, optimizador, orden de datos y aleatoriedad de esa ejecución**.

**Cobertura del corpus:** detectamos que el primer intento de continuación, `outputs/automatic`, repitió sus primeros 300 pares porque volvió a barajar con la misma semilla y reinició el cursor. Esos pares ya estaban entre los 400 vistos por el piloto. Al comenzar desde `outputs/classical-v2/best`, el controlador ahora toma también el orden y cursor guardados en `outputs/classical-v2/last` siempre que pesos, hashes de datos y parámetros coincidan. Así empieza en el par siguiente. Reinicia el optimizador si cambia la precisión o el dispositivo; es una continuación de los datos y pesos, no una reanudación numéricamente idéntica. La ejecución corregida está en `outputs/continued-unseen`.

## Qué decide el controlador

| Ajuste inicial | Valor predeterminado |
|---|---|
| Máximo de entrenamiento adicional | 3 pasadas por los pares que caben |
| Tamaño de etapa | 250 pasos |
| Checkpoint de seguridad y validación | Cada 100 pasos, fin de etapa o presupuesto |
| Validación de pérdida | 128 pares fijos, semilla 42 |
| Parada por estancamiento | 3 etapas completas sin mejorar al menos 0,01 de NLL |
| Comparación de generación | 12 frases fijas de validación, antes y después de cada invocación |
| Selección del mejor adaptador | Menor NLL de validación, incluyendo el adaptador inicial |
| Dtype | BF16 en CPU con AVX512 BF16; float32 en otros casos |

En la preparación de la corrida entregada y longitud 192 cabían 1.759 pares de entrenamiento; tres pasadas son 5.277 pasos adicionales. No se mezclan ejemplos de validación/prueba con entrenamiento, no se consultan métricas de prueba para elegir pesos y no se usan salidas del propio modelo como objetivos.

La regla de parada compara la pérdida al final de cada etapa con la mejor mejora significativa anterior. Una etapa interrumpida por presupuesto no cuenta como estancamiento. El checkpoint `best` conserva la menor pérdida observada incluso si la mejora es menor que 0,01. El informe compara además chrF++, repeticiones de trigramas y salidas truncadas. Para sugerir el adaptador nuevo exige chrF++ igual o superior, ninguna nueva salida truncada y una subida de la fracción media de trigramas repetidos de no más de 0,05 en las mismas 12 frases. Este umbral admite variaciones pequeñas: la continuación corregida obtuvo 0,028 frente a 0 inicial, mientras que la anterior produjo 0,259 y es rechazada. Es un freno de regresiones visibles, no una prueba de fidelidad.

**El presupuesto es aproximado para las etapas de entrenamiento.** Descargas, evaluación inicial/final de generación, carga de modelos y terminar una validación/checkpoint pueden añadir tiempo. No es un límite estricto de tiempo total o energía. No queda un proceso programado en segundo plano después de terminar el comando.

## Archivos y seguimiento

- `outputs/local-training/SUMMARY.md`: resumen legible y comparación de generación.
- `automation.json`: estado, etapas y política de parada.
- `train-config.json`: configuración fijada para esa ejecución.
- `run/best`: mejor adaptador; puede seguir siendo el inicial si nada mejora.
- `automation.json` → `suggested_adapter`: adaptador conservador para probar en la aplicación; `run/best` puede ser peor al generar aunque reduzca NLL.
- `run/last`: último checkpoint completo y estado reanudable.
- `train.log`: pérdidas y progreso.
- `generation-before-full.json` y `generation-after-full.json`: ejemplos y resultados para inspección local.

```bash
tail -f outputs/local-training/train.log
```

El archivo `automation.json` verifica hashes de entrenamiento, validación y prueba al continuar. Una edición del corpus o de la configuración requiere otro directorio de ejecución. Los checkpoints incluyen su informe en la misma publicación que los pesos; los archivos temporales no se consideran completos. Un bloqueo de proceso impide dos entrenamientos simultáneos sobre el mismo directorio.

Para usar explícitamente el cursor de otro adaptador `best` que coincida con su propio `last`, añade `--inherit-order-from outputs/classical-v2/last` al crear una ejecución nueva con `--init-adapter outputs/classical-v2/best`. Si los hashes de pesos no coinciden o `last` queda en un paso distinto al mejor, el entrenador rechaza la operación. Al reanudar una ejecución ya iniciada, `run/last` contiene todo el orden y ya no necesita ese argumento.

Ctrl+C conserva el último checkpoint completo. Ante un error, revisa el log y repite el mismo comando después de resolverlo. Si falla la evaluación final de una ejecución ya terminada, repetir el comando vuelve a intentar esa evaluación sin entrenar de nuevo. Si una ejecución finalizó por estancamiento o por tres pasadas, no se reinicia silenciosamente.

## Cambiar límites o equipo

Los parámetros de arquitectura, datos, etapas y parada se fijan al crear una ejecución. Al reanudar se usa la configuración guardada; solo cambia `--budget-minutes`. Para probar otro dispositivo o configuración, usa otro directorio e inicializa desde los mejores pesos existentes:

```bash
.venv/bin/python -m nahuatl_local.autotrain \
  --output outputs/segunda-prueba \
  --init-adapter outputs/local-training/run/best \
  --epochs 2 --stage-steps 250 --patience 3 \
  --device cpu --dtype float32 --budget-minutes 60
```

Esto inicia otro optimizador; no es una reanudación exacta entre dispositivos. Si MPS falla en un Mac, utiliza este patrón con CPU. Nunca necesitas una API externa para entrenar.

## Usar los pesos

No se reemplaza automáticamente el modelo de la aplicación. Para probar el adaptador elegido:

```bash
.venv/bin/python -m nahuatl_local.serve --adapter outputs/continued-unseen/run/best
```

Consulta `suggested_adapter` en `automation.json` antes de cambiar el adaptador de la aplicación. El controlador automatiza experimentos de entrenamiento, no la certificación de traducciones. Los informes están en `outputs/continued-unseen/SUMMARY.md` y `reports/RESULTADOS_2026-09-23.md`. Para seguir el estado CPU float32 entrenado aquí, usa `--output outputs/continued-unseen`; para otro equipo usa el comando principal, que crea una ejecución local adaptada a él.
