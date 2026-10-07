# Entrenamiento automático

Estado: paused_budget

La selección y parada usan validación; el conjunto de prueba no se evalúa ni se modifica.
Las métricas no certifican corrección lingüística. No se utiliza JEV ni una API.

Pasos adicionales desde el adaptador inicial: 300.
NLL inicial: 3.5783; mejor: 3.5173.
Checkpoint mejor: 250; validación: 128 pares.

| Medida de validación | Inicial | Mejor por NLL |
|---|---:|---:|
| chrF++ | 22.58 | 16.56 |
| Salidas al límite de tokens | 0 | 3 |
| Fracción media de trigramas repetidos | 0.000 | 0.259 |

La generación se inspecciona al iniciar y al finalizar cada invocación; no decide la parada ni el checkpoint.
El mejor checkpoint por NLL puede empeorar en generación. No hay promoción automática a la aplicación.
Sugerencia conservadora para experimentar: `outputs/classical-v2/best`.
Este filtro usa una muestra pequeña; no acredita traducciones correctas.

Continuar: `python -m nahuatl_local.autotrain --output outputs/automatic --budget-minutes 60`
