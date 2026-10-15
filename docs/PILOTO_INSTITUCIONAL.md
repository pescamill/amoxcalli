# Propuesta de colaboración: una lectura verificable

Versión de trabajo, 7 de octubre de 2026. No enviada a ninguna institución. No hay convenio, aval, presupuesto, participantes ni revisores institucionales confirmados. Este documento propone un piloto; no describe requisitos oficiales de admisión o certificación.

## La petición concreta

Revisar una lectura de cuatro pasajes de náhuatl clásico y probar si ayuda a principiantes a comprender un fragmento y consultar su fuente. Aves puede servir como candidata por sus preguntas de contexto; la selección final corresponde al equipo revisor. Se propone trabajar con una institución educativa o lingüística, una persona competente en la lectura histórica y un facilitador. La denominación y los roles se acordarán con la contraparte.

Una institución mexicana podría evaluar el proyecto como herramienta de lectura y edición documental. Para una colaboración con hablantes actuales, la propuesta debe partir de una comunidad y variedad elegidas por sus participantes; no trasladar automáticamente los textos clásicos a un curso contemporáneo.

## Paquete disponible para examinar

| Material | Dónde encontrarlo | Qué demuestra |
| --- | --- | --- |
| Aplicación local | `bash scripts/amoxcalli.sh serve` | Un recorrido funcional, sin necesidad del LLM |
| Propósito y límites | [PROPOSITO](PROPOSITO.md) y pantalla Proyecto y colaboración | Alcance declarado y públicos previstos |
| Ficha de lectura | Leer → Preparar ficha para taller; `#taller/aves` | Pasajes, preguntas, claves opcionales, localizadores y hashes |
| Receta y respaldo | `configs/reading-context-2026-10-07.json` y `reports/learning-before-reading-context-2026-10-07/` | Conservación del contenido original y decisiones reproducibles |
| Revisión pendiente | [Plan vigente](ROADMAP.md), auditoría de lecturas y notas de cada ficha | Dudas visibles; no revisión especializada concluida |
| Condiciones del contenido | [Fuentes](FUENTES.md), [Voces](VOCES.md), THIRD_PARTY_NOTICES | Separación de permisos; revisión de derechos pendiente por obra y uso |
| Funcionamiento técnico | `make test` (suite Python y DOM) | Pruebas técnicas; no evidencia de aprendizaje ni certificación |

## Trabajo propuesto en seis semanas

Calendario indicativo a acordar según disponibilidad. Puede pausarse o reducirse.

1. **Acuerdo de alcance.** Elegir lectura y población, responsables, reconocimiento o remuneración, permisos, custodia de datos y condiciones de retiro. Definir cómo se informará a participantes y quién autoriza cada actividad. Si faltan permisos o responsables, no iniciar la prueba con personas.
2. **Cotejo de cuatro pasajes.** Revisar original, edición/traducción, localizador y alcance de cada vínculo visual. Registrar decisiones y desacuerdos con fuentes; retirar del piloto cualquier afirmación sin respaldo suficiente.
3. **Revisión didáctica.** Comprobar que las preguntas se responden con el pasaje, que los distractores no inducen ideas falsas y que las ayudas permiten distinguir palabras de componentes. Revisar navegación con teclado y lectura en un teléfono; todavía no se declara conformidad de accesibilidad.
4. **Taller acompañado.** Propuesta inicial: seis a ocho personas adultas, una sesión de 20–30 minutos. Puede usarse papel o una instalación local; no solicitar aportaciones al entrenamiento para participar. La muestra sirve para descubrir dificultades, no para generalizar resultados.
5. **Corregir y repetir.** Resolver los problemas observados, repetir los puntos que fallaron y conservar diferencias entre versiones.
6. **Devolver resultados.** Entregar a participantes y contraparte la lectura revisada, incidencias, decisiones, evidencias, restricciones y recomendación de continuar, cambiar de rumbo o detener la ampliación.

## Evaluación propuesta

Se acuerdan criterios antes del taller. La evaluación puede ser anónima en papel; no se añade telemetría ni se transmiten datos desde la aplicación.

| Pregunta | Observación | Criterio inicial propuesto |
| --- | --- | --- |
| ¿Puede orientarse? | Abre lectura, fuente y repaso con contexto | Al menos seis de ocho completan el recorrido con un máximo de una indicación; ajustar si cambia la muestra |
| ¿Comprende algo nuevo? | Explica en sus propias palabras un fragmento no usado en el ejercicio, elegido y revisado por el docente | Registrar evidencia por persona antes/después con la misma rúbrica; analizar qué ayuda y qué confunde, sin prometer mejora |
| ¿Distingue evidencia de asociación? | Explica por qué una imagen relacionada no equivale a toda una palabra u oración | Al menos seis de ocho distinguen ambos alcances tras la actividad |
| ¿Es verificable? | Revisor encuentra fuente y localizador; coteja el ejemplo | Cuatro de cuatro pasajes con revisión registrada y derechos resueltos para el uso del piloto |
| ¿Hay problemas críticos? | Errores lingüísticos, permisos insuficientes o pérdida de datos | Ningún problema crítico sin resolver antes de recomendar la lectura |

Estos umbrales son decisiones de diseño propuestas, no estándares del INALI ni prueba estadística de eficacia. La rúbrica de comprensión debe acordarse con el docente: sentido central, evidencia citada y duda identificada. Una observación de hablantes actuales no sustituye el cotejo histórico; un especialista histórico tampoco decide por una comunidad la enseñanza de su variedad actual.

## Pendientes y responsabilidades

| Pendiente | Responsable a acordar | Evidencia necesaria |
| --- | --- | --- |
| Revisión histórica y didáctica | Revisor lingüístico y docente | Nombre/identificador autorizado, fecha, decisiones y fuentes |
| Derechos de obras, traducciones e imágenes | Responsable editorial con asesoría competente cuando corresponda | Permiso o fundamento documentado para el uso concreto; exclusiones explícitas |
| Consentimiento, custodia y retiro | Responsable de la instalación y contraparte | Acuerdo comprensible, destino de datos, plazos y procedimiento |
| Reconocimiento o remuneración | Coordinación y participantes | Acuerdo previo y presupuesto si se requiere |
| Instalación y respaldos | Responsable técnico | Prueba en el equipo real, copia de seguridad y recuperación |
| Evaluación y devolución | Facilitador y participantes | Rúbrica, resultados agregados sin datos identificables y lista de mejoras |

Todos estos responsables están por confirmar. Los documentos y pruebas existentes son un punto de partida, no evidencia de que esas responsabilidades ya estén atendidas.

## Referencias públicas y relación institucional

El [catálogo INALI](https://www.inali.gob.mx/sitios/clin-inali/) documenta variantes y autodenominaciones. Su recurso sobre [diversidad lingüística y escritura](https://constitucionenlenguas.inali.gob.mx/lenguas-originarias) describe acuerdos de hablantes con asesoría del Instituto. Se consultaron el 7 de octubre de 2026 como referencias de diseño; no se solicitaron ni obtuvieron avales.

Antes de presentar una propuesta a INALI, a una institución educativa o a un área cultural de un gobierno local, verificar su competencia, canal de colaboración y requisitos vigentes. No añadir logos, afiliaciones, aprobación gubernamental ni denominaciones de certificación sin autorización documentada. La primera petición debería ser revisar este piloto concreto con la contraparte adecuada.
