# Verificación del coordinador · ciclo 007

El validador final reprodujo la recuperación y admitió la comparación actual. Se comprobaron independientemente los tres estados, las métricas y costes contra el informe medido, los valores `null` de los modelos sin ejecutar, los hashes actuales y la repetición del diagnóstico. Las 123 respuestas coinciden con el snapshot 006; corpus, batería y recuperador conservan sus hashes. Historia, decisiones y prefijos de notas/snapshots permanecen intactos. [Evidencia calculada](iterations/iteration-007/coordinator-verification.json).

En el navegador se verificaron los tres métodos, los denominadores 119/123 y 121/121 respuestas frente a 121/123 casos, los costes ausentes y la separación de resultados históricos. Se abrió el detalle de los cuatro fallos y se reprodujo una abstención de A desde su enlace. No se guardaron palabras ni se cambió el progreso. La anchura del contenido coincide con la visible: 1.265 px. [Captura de la pantalla final](iterations/iteration-007/laboratory-browser.jpg).

Las dos descargas públicas se verificaron por HTTP en el servidor habitual: contienen agregados y fallos observados, sin arrays de referencias esperadas ni casos reservados. El primer intento de conexión fue bloqueado por sandbox; la repetición con aprobación automática pasó. El servidor quedó actualizado con el mismo comando y configuración, sin ejecutar inferencia.

Pasan 230 pruebas con un fallo esperado heredado, 31 dirigidas, once grupos DOM/HTTP y privacidad offline. Las pruebas heredadas con modelos mínimos sintéticos temporales no constituyen una nueva corrida del modelo publicado. La medición y la verificación documental utilizan fuentes públicas y bases temporales; el arranque normal conserva la persistencia habitual de la aplicación.

Ambos README reflejan el estado actual. Se cubren los hitos iniciales de preparación técnica; quedan 66 tareas humanas. Esto no declara competencia del LLM, evaluación multimodal, revisión lingüística ni eficacia educativa. El siguiente paso es revisar una lectura completa y probar comprensión con principiantes.
