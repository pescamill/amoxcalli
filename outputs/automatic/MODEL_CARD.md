# Intento de continuación anterior (descartado)

Qwen3-0.6B + LoRA, inicializado desde el adaptador `outputs/classical-v2/best` de 400 pasos. Se realizaron 300 pasos adicionales con CPU float32 y optimizador nuevo; el mejor checkpoint por NLL está en el paso adicional 250. La NLL sobre 128 pares de validación bajó de 3,5783 a 3,517 aproximadamente, pero la generación empeoró.

Este intento reinició el cursor usando el mismo orden barajado que el piloto: los 300 pasos nuevos consumieron pares ya vistos en los primeros 400 pasos. Es una causa posible del deterioro, no una causalidad demostrada. En 20 frases de prueba, chrF++ fue 9,54 frente a 16,03 para el piloto; hubo 12 salidas truncadas frente a 2. `automation.json` marca el filtro de generación como fallido. No se recomienda usar `run/best` para la aplicación. `run/last` conserva el estado para reproducir e inspeccionar el intento.

Consulta `reports/RESULTADOS_2026-09-23.md` para la continuación con cursor corregido. Los resultados son experimentales y no están validados por especialistas. Base Apache-2.0; código original MIT; derechos del corpus y pesos derivados sujetos a revisión. Consulta `THIRD_PARTY_NOTICES.md` y `docs/FUENTES.md`.
