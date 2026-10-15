# Preguntar con evidencia

`#preguntar` responde una palabra o una pregunta breve («nocal», «kuali», «¿qué significa xochitl?», «¿cómo se dice mujer?») con evidencia del propio proyecto. Es recuperación, sin LLM: no genera traducciones nuevas.

## Qué reúne

| Pieza | De dónde sale | Cómo se presenta |
|---|---|---|
| Análisis | `morphology.Analyzer` (reglas + diccionario + EM sobre el corpus) | Segmentación con su base declarada |
| Entradas | Diccionario público: forma igual por clave laxa, o entrada de la raíz | «misma palabra», «otra grafía», «misma raíz» |
| Pasajes clásicos | `stems.StemConcordance`, misma raíz aunque cambien afijos | Forma resaltada, traducción del archivo, ID |
| Otras variedades | Índice por clave laxa sobre los 16.111 pasajes | Agrupados por variedad; el analizador solo cubre el clásico |
| Español → náhuatl | Modelo IBM‑1 de `stems.GlossHints` invertido (apoyo ≥ 8 pasajes, p ≥ 0,3) | «el corpus paralelo lo traduce así», con formas y pasajes; no es una definición |

Sin raíz con apoyo suficiente, una palabra española muestra pasajes cuya traducción la contiene, sin proponer equivalente. Sin entradas ni pasajes, la respuesta se abstiene.

## Clave laxa

`evidence.loose_key` parte de la clave fonémica del analizador y además une `kw`/`cu`/`qu`, `ts`/`tz`, quita `j` (saltillo moderno), reduce consonantes dobles (`ll`, `tt`, `nn`) y trata `-uh` final como `-u`. Así *kuali*, *cualli* y *qualli*, *tlajtoli* y *tlahtolli*, o *kali* y *calli* llegan a los mismos pasajes. Se usa solo para recuperar; la clave evaluada del analizador no cambia.

## Medición

```bash
.venv/bin/python -m nahuatl_local.evidence_evaluation --split dev   # para ajustar
.venv/bin/python -m nahuatl_local.evidence_evaluation               # informe completo
```

[Informe vigente](../reports/EVIDENCIA_EVALUACION.md); [primera corrida con la prueba](../reports/evidence-evaluation-first-test-run.md). Conjunto: `evaluation/evidence-questions-v1.json`, 17 consultas de desarrollo y 32 de prueba escritas después. Línea base: la búsqueda literal anterior (forma escrita o definición; pasajes con la palabra completa).

En prueba, la entrada esperada aparece primero en 92 % de las consultas (base 42 %), siempre hay al menos un pasaje pertinente (base 76 %) y la precisión de pasajes es 94 % (base 84 %). Las grafías modernas pasan de 0 % a 100 % de entradas correctas. Fallan *atlan* y *michime* (el analizador no los enlaza a *atl* y *michin*) y *pájaro* (asociación débil). *teléfono* y *automóvil* estaban etiquetadas como abstención, pero el archivo sí las traduce en pasajes de Morelos; las etiquetas se conservaron con una nota.

La pertinencia se decide automáticamente (raíz esperada en una palabra del pasaje). Mide recuperación, no corrección lingüística; las respuestas siguen pendientes de revisión.

## Límites conocidos

- Homógrafos de raíz: *tlacualli* («comida») aparece junto a *cualli* («bueno») porque comparten la raíz analizada.
- Nombres propios leídos como poseídos (*Mo-tecuhzoma*) y otros errores del analizador; ver el paso 2 de [ROADMAP](ROADMAP.md).
- Las palabras sin entrada en el diccionario (*cihuatl*, *tlacatl*) dependen de los pasajes y de las pistas del corpus.

Endpoint: `GET /api/ask?q=…`. Siguiente paso previsto: una capa opcional que redacte explicaciones citando solo esta evidencia, validada por el comprobador de citas.
