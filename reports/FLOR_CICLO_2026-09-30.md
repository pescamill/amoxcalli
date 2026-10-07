# Primer ciclo editorial: flor · versión 2

30 de septiembre de 2026. El paquete flor se revisó como piloto editorial local. El cambio mejora conexiones y ejercicios; no declara cotejo primario, certificación lingüística ni prueba realizada con principiantes.

## Resultado concreto

- cuicatl tiene entrada propia: se seleccionó únicamente GDN 38566, Molina parte 2. La forma paleográfica `Cuicatl`, la normalizada `cuicatl` y la glosa histórica se guardan separadas. Se añadió ayuda en los dos pasajes que la contienen.
- Cacahuaxochitl tiene entrada propia y la palabra completa ya no apunta a la acepción simple de xochitl. Se conserva la traducción heredada del corpus. El catálogo Oregon advierte que la denominación tradicional no equivale a identificar la flor del árbol del cacao; la lección evita deducir una especie.
- Su imagen se enlaza a la ficha nominal de Ágata Cacahuaxochitl, Matrícula de Huexotzinco, f. 885v. Se explica que pertenece a otro documento. La clasificación simplex/compound difiere dentro del catálogo: se conserva `unspecified` hasta cotejo.
- NIQUITTA permanece intacta, enlazada editorialmente a itta y marcada con análisis pendiente. La ayuda explica que Tlachia es una comparación semántica, no la lectura de NIQUITTA.
- xochitli permanece intacta; el último ejercicio pide esa grafía exacta. Su relación con xochitl se identifica como pendiente de cotejo, sin crear una forma supuestamente verificada.

Fuentes consultadas: [Molina vía GDN, entrada 38566](https://gdn.iib.unam.mx/contexto/38566), [cuicatl en Oregon, con localizador f. 26v, col. 1](https://nahuatl.wired-humanities.org/content/cuicatl), [cacahuaxochitl en Oregon](https://nahuatl.wired-humanities.org/content/cacahuaxochitl), [Cacahuaxochitl MH885v en VLA](https://aztecglyphs.wired-humanities.org/content/cacahuaxochitl-mh885v). El catálogo remite al [Florentino, libro 11, f. 188v](https://florentinecodex.getty.edu/book/11/folio/188v). Consultar estas referencias no se registra como cotejo de los pasajes poéticos contra su edición primaria.

## Claves y objetivo

| Registro | Clave | Justificación | Alcance |
|---|---|---|---|
| axolotl-05338 | Una flor | Traducción heredada del título | Comprensión del registro, no análisis de NIQUITTA |
| axolotl-06231 | xochitl | Coincide exactamente con la forma del pasaje | Recuperación de la forma |
| axolotl-10445 | Cacahuaxochitl | Palabra completa del registro | Distinguirla de xochitl y cuicatl; no preguntar especie botánica |
| axolotl-13493 | xochitli | Coincide exactamente con la grafía fuente | Preservar grafía; xochitl es un distractor distinto |

Los cuatro textos, traducciones, IDs y hashes se conservan. Cielo y lugares se conservan sin cambios. Solo flor recibe versión 2: se reinicia su práctica para esta edición; el progreso de las otras lecciones sigue ligado a versión 1. La validación rechaza claves de cloze que no recuperen el texto exacto y referencias visuales asignadas a otra acepción. La auditoría busca formas por acepción, no únicamente por homografía en cualquier ficha.

## Mecanismo y preservación

`corpus/flor-lexicon-v8.json` añade cinco registros mediante migración aditiva e idempotente. Se conservaron exactamente las 1.173 entidades anteriores, sus versiones/fechas, historial, perfiles y aportaciones. Catálogo actual: 1.178 entidades, 525 acepciones, 528 formas, 101 referencias glíficas, 20 fuentes, 3 textos y 1 nota. Hay 100 acepciones con imagen y 425 pendientes; las 24 representativas siguen en la primera página. Evidencia: [data-preservation-flor-v8.json](data-preservation-flor-v8.json). Respaldo privado: `data/backups/voces-before-flor-v8.sqlite3`, permisos 0600.

La extracción de cuatro búsquedas GDN se reproduce mediante `scripts/extract-flor-sources.py`: utiliza caché local por defecto; `--fetch` obtiene páginas faltantes. Con la caché presente no usa red ni LLM. Preserva hashes de páginas y rechaza páginas inesperadas, distinguiéndolas de resultados vacíos declarados. La selección de una entrada exacta se mantiene separada de una búsqueda por prefijo: los diez resultados de cuicatl no se convierten en diez importaciones.

```bash
.venv/bin/python scripts/extract-flor-sources.py
.venv/bin/python -m nahuatl_local.lesson_audit
```

`editorial/lesson-decisions.json` conserva decisiones y el hallazgo original cuando el vacío desaparece de la cola. La auditoría muestra esos antecedentes por separado y exige su fingerprint válido; ausencia de un hallazgo no significa aprobación. La decisión de ejercicios es una revisión editorial/técnica de claves, no una evaluación pedagógica con personas. El LLM y sus datos de entrenamiento no cambiaron.

## Lo que falta

1. Localizar la edición y página de cada uno de los cuatro pasajes poéticos; el archivo ofrece registro, pero no sustituye ese cotejo.
2. Revisar lingüísticamente NIQUITTA e xochitli y los enlaces a sus acepciones. No se añaden fichas de formas para hacer desaparecer estas tareas artificialmente.
3. Cotejar el uso nominal y el alcance floral de la nueva referencia visual; obtener una referencia propia de cuicatl si existe, sin forzar una imagen temática a equivaler a la palabra.
4. Ejecutar y registrar el [ensayo con principiantes preparado](../editorial/flor-beginner-trial.md).

La cola actual conserva 26 tareas: 1 resuelta editorialmente, 4 bloqueadas por evidencia/revisión/participantes y 21 abiertas; hay otras 2 decisiones resueltas en el historial porque sus vacíos de catálogo ya desaparecieron. El aumento a 10 acepciones objetivo es explícito: se añadieron canto y el nombre floral completo. Cobertura visual de estas acepciones: 9/10 con imagen, 0/10 con contexto primario declarado. cuicatl puede enseñarse mediante evidencia textual mientras su referencia visual siga pendiente.

## Comprobación

La suite completa ejecutó 160 pruebas con éxito y una falla esperada previamente registrada. Las seis comprobaciones de interfaz pasaron, incluyendo entradas nuevas, ayuda contextual, respuesta incorrecta, grafía exacta, progreso, guardado y orden del diccionario. Se observó la ayuda nueva en el navegador y su imagen de fuente carga. Informes: [tests-flor-full-2026-09-30.txt](tests-flor-full-2026-09-30.txt), [platform-ui-flor-2026-09-30.txt](platform-ui-flor-2026-09-30.txt).
