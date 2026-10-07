# Entrenamiento automático

Estado: paused_budget

La selección y parada usan validación; el conjunto de prueba no se evalúa ni se modifica.
Las métricas no certifican corrección lingüística. No se utiliza JEV ni una API.

Pasos adicionales desde el adaptador inicial: 250.
NLL inicial: 3.5783; mejor: 3.5302.
Checkpoint mejor: 250; validación: 128 pares.

| Medida de validación | Inicial | Mejor por NLL |
|---|---:|---:|
| chrF++ | 22.58 | 27.96 |
| Salidas al límite de tokens | 0 | 0 |
| Fracción media de trigramas repetidos | 0.000 | 0.028 |

La generación se inspecciona al iniciar y al finalizar cada invocación; no decide la parada ni el checkpoint.
El mejor checkpoint por NLL puede empeorar en generación. No hay promoción automática a la aplicación.
Sugerencia conservadora para experimentar: `outputs/continued-unseen/run/best`.
Este filtro usa una muestra pequeña; no acredita traducciones correctas.

Continuar: `python -m nahuatl_local.autotrain --output outputs/continued-unseen --budget-minutes 60`
