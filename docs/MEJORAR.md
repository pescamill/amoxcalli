# Continuar y mejorar el modelo

Prioridad educativa acordada el 30 de septiembre de 2026: [iterar lecciones y conexiones revisadas](LEARNING_ITERATION_PLAN.md) antes de otra corrida. Los comandos siguientes se conservan como referencia técnica; el [primer ciclo flor](../reports/FLOR_CICLO_2026-09-30.md) ya se ejecutó y no incorpora entrenamiento. Cotejo lingüístico/primario y prueba con principiantes siguen pendientes.

El flujo recomendado ahora está automatizado en [AUTOTRAIN.md](AUTOTRAIN.md): `bash scripts/autotrain.sh --budget-minutes 60`. Las secciones siguientes describen los comandos manuales y la revisión posterior.

El crecimiento educativo ya dispone de un [pipeline por lotes](EDITORIAL_PIPELINE.md): fuentes cacheadas → candidatos priorizados → revisión compartida y excepciones → lote validado → publicación aditiva con respaldo. `run --release-id NUEVO_ID` prepara y coteja; `--apply` incorpora el lote. Ya se publicaron 50 entradas y 39 apoyos contextuales, con preservación de los datos existentes. No usa el LLM ni modifica el entrenamiento.

## Estado de datos al 29 de septiembre de 2026

La preparación actual cambió respecto a los pesos entregados. Los hashes de `data/prepared` ya no coinciden con `outputs/continued-unseen`: no reanudar esa corrida ni heredar su orden sobre estos datos. Conservar los checkpoints y crear una ejecución nueva con `--init-adapter`, sin `--inherit-order-from`, después de revisar y evaluar la preparación actual. La reanudación exacta de la sección 2 solo aplica si se restauran los archivos de datos originales y sus hashes. El laboratorio muestra esta diferencia.

Para ampliar las lecturas guiadas, el [ensamblador de lecturas](LECTURAS_PIPELINE.md) transforma recetas explícitas con IDs de archivo en recorridos con hashes, formas verificadas y claves cloze exactas, preservando los ejercicios anteriores. Lecturas-002 añadió 3 recorridos y corrigió confusiones de imagen/compuesto/contexto; no actualizó los pesos.

## 1. Continuar en tu computadora

Tras instalar y descargar según README, inicia una ejecución nueva usando los pesos entregados:

```bash
python -m nahuatl_local.train --init-adapter outputs/continued-unseen/run/best \
  --output outputs/mi-modelo --steps 1759
```

Conserva los pesos como inicialización y crea un optimizador y un orden nuevos sobre la preparación actual. No conserva el cursor de la corrida anterior: su corpus tiene hashes distintos. La configuración predeterminada usa float32 y elige CUDA, MPS o CPU según disponibilidad. En un Mac M4 puedes probar la selección automática; usa `--device cpu` si MPS falla. Solo CPU fue comprobada aquí. No hace falta comprar hardware antes de probar.

El archivo `configs/train.json` controla longitud, learning rate, rank y número de pasos. Se omiten pares que exceden el límite; no se truncan traducciones silenciosamente. Aumentar 192 a 256/384 puede incluir más pares, pero aumenta memoria y cómputo. Cambiar rank o módulos exige un nuevo adaptador, no inicializar desde uno incompatible.

## 2. Reanudar exactamente

La continuación más reciente se entrenó en CPU float32. Para continuar exactamente su estado y sus pasos adicionales en hardware compatible:

```bash
python -m nahuatl_local.autotrain --output outputs/continued-unseen --budget-minutes 60
```

El piloto BF16 se puede reanudar por separado con `python -m nahuatl_local.train --config configs/train-cpu-bf16.json --resume outputs/classical-v2 --steps 1759 --eval-every 200` en CPU compatible. En el entrenador manual, `--steps` es el total de pasos de **esa ejecución**. `last/state.pt` incluye optimizador, orden de ejemplos y estados aleatorios; `best/` sirve para inferencia. La configuración y hashes de los datos se verifican al reanudar. No cambies dtype ni datos al reanudar: usa una ejecución nueva con `--init-adapter` si necesitas hacerlo.

Ctrl+C conserva el último checkpoint completo, no necesariamente cada paso desde él. La escritura conserva una versión anterior hasta publicar pesos y estado juntos. La prueba automática compara cuatro pasos continuos con dos más dos reanudados en un modelo diminuto; no promete identidad entre dispositivos.

En la preparación histórica, con acumulación 1, una pasada por los 1.759 pares que cabían equivalía a 1.759 pasos. La corrida nueva debe calcular su propio número de pares admisibles. No cuenta validación/prueba. Más entrenamiento no garantiza generalización; detente si la validación se estanca o empeora.

## 3. Evaluar antes de cambiar más cosas

La preparación actual usa `nah-ortho-1` y contiene 5.462 pares. Los informes de generación anteriores describen otra preparación y una muestra exploratoria de 20 frases. Para medir la recuperación actual sin cargar el LLM:

```bash
python -m nahuatl_local.benchmark --retrieval-only --split validation --limit 100 \
  --output reports/mi-recuperacion-full.json
```

La referencia de 29 de septiembre está en [benchmark-retrieval-validation-current.json](../reports/benchmark-retrieval-validation-current.json): 100 ejemplos, 99 sin solapamiento detectado, chrF++ de recuperación 16,01 (16,08 sin el ejemplo señalado), con 1.000 remuestreos y dos obras. El intervalo del 95% por obra es 12,74–19,14; dos obras ofrecen una cobertura limitada. El índice contiene exclusivamente las 2.161 filas de entrenamiento. Esta cifra no mide al generador ni permite comparar directamente con la recuperación antigua de 27,20 en test.

Cada informe guarda hashes, configuración, predicciones y una hoja de revisión humana. Para comparar el generador con recuperación, ejecuta ambos en la misma preparación, split y selección. Usa prueba después de elegir la configuración mediante validación.

```bash
python -m nahuatl_local.benchmark --split validation --adapter outputs/mi-modelo/best --limit 50 --output reports/mi-validacion-full.json
```

Usa validación para comparar configuraciones. Reserva prueba para versiones elegidas previamente. chrF++ es similitud textual, no porcentaje de traducciones correctas. Revisa 50 frases con alguien competente en náhuatl clásico: significado, persona/número, negación, posesión, tiempo/aspecto, valencia y ortografía. Registra correcciones con su fuente, no preferencias estéticas.

Las antologías pueden compartir poemas aunque sean obras distintas. La heurística del benchmark busca semejanza de secuencias de palabras en ambos idiomas; no identifica todas las paráfrasis o variantes ortográficas. Antes de afirmar generalización, agrupa también por poema/pasaje original y crea una prueba revisada. La partición actual deja ~40% de los pares en entrenamiento porque reserva obras grandes; una partición futura más equilibrada requiere rehacer la evaluación, no mover el test a entrenamiento y seguir citando sus puntuaciones.

## 4. Añadir pares revisados

Completa `templates/reviewed.csv`: español, náhuatl, obra, edición/página/folio, URL, licencia, revisor e ISO `nci`. No uses borradores del modelo como respuestas correctas. Los permisos deben corresponder también a la traducción y edición, no solo al manuscrito antiguo.

```bash
python -m nahuatl_local.curate templates/reviewed.csv --output data/curated-v3
```

El importador conserva validación/prueba, rechaza obras reservadas, duplicados y filas incompletas. No puede autenticar las licencias o la revisión declaradas ni detectar todos los alias de títulos. Copia `configs/train.json` a `configs/curated-v3.json`, cambia `data` a `data/curated-v3` y `output` a `outputs/curated-v3`:

```bash
python -m nahuatl_local.train --config configs/curated-v3.json --init-adapter outputs/continued-unseen/run/best
python -m nahuatl_local.serve --data data/curated-v3 --adapter outputs/curated-v3/best
```

## 5. Mejorar la evaluación humana

`templates/review_labels.csv` permite recoger juicios humanos sobre candidatos y evidencias. Mantén separados los juicios humanos y las reglas locales; una coincidencia textual no es una etiqueta lingüística verificada.

Con suficientes juicios revisados se puede entrenar un evaluador local propio y medir falsos positivos por tarea. Todavía no está entrenado. Mientras tanto, los juicios desconocidos quedan en `null` y se solicita revisión humana.

La siguiente prueba concreta es completar una pasada, medir validación y revisar errores. Si no mejora, corrige alineaciones y cobertura antes de repetir épocas. Ni un modelo mayor ni una métrica automática resuelven por sí solos un corpus insuficiente.

## 6. Inglés y fuentes verificadas

El generador actual recibe español. Para añadir inglés, reúne pares inglés–náhuatl revisados y con permisos claros, manteniendo el identificador del pasaje original. Agrupa sus versiones española e inglesa en la misma partición para evitar que una traducción del test aparezca en entrenamiento. Después añade el idioma de entrada al prompt, el importador y la evaluación; mide inglés por separado. Traducir automáticamente el español al inglés puede producir candidatos para revisión, no referencias certificadas. No se incluye aún ese segundo entrenamiento.

Para mejorar las citas, el siguiente dato útil es una alineación revisada entre cada pasaje, su edición y página/folio. La recuperación actual remite a registros del corpus y catálogos, pero no verifica cada transcripción contra el manuscrito. Una ficha glífica requiere además identificador de imagen, códice, folio, lectura y responsable de la interpretación. Las reglas automáticas no sustituyen esta comprobación documental. Mantén el texto generado marcado como borrador incluso cuando incluya enlaces.


## Proponer pares desde el laboratorio

La pestaña [Datos de entrenamiento](http://127.0.0.1:8766/#modelos/datos) muestra los 650 pares recorridos por el adaptador y permite proponer pares manualmente o por CSV con procedencia y permisos. Las propuestas quedan privadas, pendientes; solo se exportan después de revisión lingüística y de derechos por el responsable. La exportación puede entrar en `nahuatl_local.curate` hacia un directorio nuevo, preservando validación y prueba. [Flujo y comandos](LABORATORIO.md). La ampliación automática del diccionario no añade entrenamiento ni otorga permiso para usar las fichas en los pesos.
