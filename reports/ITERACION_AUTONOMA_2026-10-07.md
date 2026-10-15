# Inicio de la iteración autónoma

7 de octubre de 2026. El usuario autorizó iniciar ahora, aumentar la frecuencia y usar GPT-6.1 Sol con razonamiento high.

## Continuidad y modelo

La automatización `iterar-amoxcalli-gpt-6-1-sol-high` está activa cada 30 minutos y retoma este chat. La propuesta diaria anterior no se había activado; se creó una sola automatización. Se verificó su estado ACTIVE, frecuencia y chat de destino mediante la herramienta y su configuración guardada.

El seguimiento de un chat no admite parámetros directos de modelo. Su instrucción delega cada implementación a un único agente con `model=gpt-6.1-sol`, `reasoning_effort=high` y contexto explícito. Este ciclo utilizó ese agente; el coordinador revisó el resultado. No se afirma haber cambiado el modelo del coordinador ni el LLM del producto.

Hasta 48 activaciones diarias dependen del equipo encendido, la aplicación abierta y los límites disponibles. Se retoma trabajo activo sin lanzar otro escritor. Un objetivo persistente mantiene los hitos de la primera fase técnica; su estado continúa activo.

## Dos resultados locales

1. Un diagnóstico reproducible de fuentes públicas y una cola persistente. Conserva decisiones e historia, detecta informes obsoletos y reabre decisiones cuya evidencia cambió. No utiliza la base privada de Voces. [Guía](../docs/ITERACIONES.md), [diagnóstico inicial](iterations/iteration-001/inventory.md) y [diagnóstico posterior](iterations/iteration-002/inventory.md).
2. La importación aditiva de Telleriano 385_26v: 31 apariciones, 68 componentes y 26 elementos nuevos; 18 elementos reutilizados. Se corrigió el rechazo de elementos idénticos documentados desde otra lámina, preservando íntegramente la ficha original. [Informe del lote, respaldo y comandos](iterations/iteration-002/changes.md).

El índice contiene 3 conjuntos, 4 láminas, 77 denominaciones, 87 registros de elementos y 91 apariciones: 77 glifos y 14 personajes. Se conservan 6 lecturas, 24 pasajes, 575 acepciones y 578 formas. La publicación repetida y el diagnóstico repetido conservaron sus bytes.

## Verificación y alcance

Las 24 pruebas específicas de pictografía, diagnóstico y auditoría pasaron; también los recorridos DOM y la comprobación sin conexión. En el navegador se verificaron los nuevos conteos, denominaciones y enlaces a la lámina nueva. La captura se conserva temporalmente en `/private/tmp/amoxcalli-iteracion-002.jpg` y se presenta en el chat.

La suite completa detectó una expectativa HTTP fijada en 46 glifos. La prueba ahora verifica el conteo de las apariciones del catálogo vigente, permitiendo ampliaciones aditivas. La nueva corrida terminó con **200 pruebas, OK y un fallo esperado existente**; su resultado está en [el informe completo](tests-autonomous-2026-10-07.txt).

Estos resultados acreditan funcionamiento y conservación documental. La revisión especializada, el cotejo primario y los ensayos con personas siguen pendientes. El índice mantiene `training:false`; no hubo entrenamiento ni descargas de pesos. No se hicieron commits ni publicaciones externas.

## Siguiente paso

La cola actual tiene 41 tareas: 35 abiertas, 4 bloqueadas, 1 resolución editorial heredada y 1 técnica en progreso. Se debe ampliar el diagnóstico para incluir preparación de las seis lecturas adicionales, recuperación, evaluación textual/visual y Laboratorio, con criterios verificables y estados separados de revisión humana. Después, preparar el siguiente lote o lectura sustentado en fuentes admitidas. La meta de 300 apariciones todavía tiene un faltante de 209.
