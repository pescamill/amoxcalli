# Dioses y calendario

Fichas de deidades, figuras, epítetos y lugares; el tonalpohualli (20 signos × 13 numerales, 20 trecenas) y el
xiuhpohualli (18 veintenas y nemontemi). Generado por `nahuatl_local/entities.py`, sin modelo ni red.

## Fuentes y procedencia por dato

`corpus/entities-seed-v1.json` es lo que escribe el proyecto. Cada atributo, relación, glosa, posición o nombre lleva
`sources`, y el generador comprueba cada una antes de escribir:

| Fuente | Qué se comprueba | Licencia |
|---|---|---|
| Pasaje de Axolotl (`passage` + `quote`) | la cita está literalmente en el náhuatl del pasaje; el pasaje no es de una obra restringida | MPL-2.0 del distribuidor; auditar cada obra antes de redistribuir |
| Acepción del catálogo (`sense`) | existe en el catálogo léxico; Wiktionary trae su revisión y atribución | CC BY-SA 4.0 (Wiktionary) o texto del proyecto |
| Revisión fijada de Wiktionary (`wiktionary`) | página y `oldid` registrados en la semilla (consulta del 16 oct 2026) | CC BY-SA 4.0 |
| Tlachia (`tlachia_reading`, `element`) | la lectura o el elemento existe en `corpus/pictography/catalog.json` | consulta con atribución; imágenes desde su sitio |

**Nada del Códice Florentino** hasta tener permiso: *Vida económica de Tenochtitlan* (libro IX de Sahagún) y tres pasajes
del libro XII y del VI (`restricted_passages`) se cuentan pero no se muestran ni se usan en lecturas. Las citas del
Florentino que Tlachia trae en sus fichas no se copian. **Sin imágenes generadas.**

## Qué genera el módulo

* **Grafías**: el índice de términos da el grupo de cada nombre y sus grafías con la misma clave laxa (`text.loose_key`);
  las formas flexionadas e inciertas no cuentan. Una grafía que las fichas no reúnen pasa por el buscador de grafías
  ([GRAFIAS.md](GRAFIAS.md)): *Huitzilopoxtli* o *Kwetsalkowatl* llevan a la ficha como «posible grafía», con su
  motivo y confianza. Los nombres de varias palabras (*Tloque Nahuaque*, *xocotl huetzi*) se buscan como frase. Una grafía que llevara a dos fichas detiene la generación. *Itztli* (obsidiana) no lleva a la ficha
  del Señor de la Noche.
* **Pasajes**: los del archivo con esas grafías; la ficha muestra hasta 8 pasajes clásicos alternando obras.
* **Tlachia**: Señores de la Noche (`yohualteuctli : X`), figuras de lámina (`inacayo : X`) y atavíos, con folio e imagen.
* **Calendario**: los 99 glifos de días del Telleriano-Remensis fijan la trecena de 10 láminas; si el orden de los signos
  de la semilla fuera otro, alguna lámina no formaría una sola trecena y la generación fallaría. Los nombres calendáricos
  del archivo (numeral + signo) dan los pasajes de cada día; son seguros si la traducción da el número.
* **Veintenas**: posición por ordinal de Wiktionary, por la secuencia de Chimalpahin (axolotl-01746, 02334) o como hueco
  entre dos posiciones con fuente. **Teotleco y nemontemi no tienen fuente abierta para el nombre**: la ficha lo dice.

## Interfaz y API

«Más → Dioses y calendario» (`#dioses`, `platform_web/gods.js`): fichas con fuentes y folios de Tlachia, trecena → día →
día siguiente, signos, numerales, veintenas, lecturas y la unidad. Preguntar enlaza la ficha si la consulta nombra una
entidad o un día; Lecturas muestra un bloque. Rutas (`entities.routes`): `/api/entities`, `/api/entities/<id>`,
`/api/entity-search?q=`, `/api/calendar/day?n=&sign=` (sign de 0 a 19), `/api/calendar/unit`. Prueba DOM:
`scripts/test-gods-ui.py`.

## Lecturas, unidad y revisión

* Cuatro lecturas de mitología (`configs/lecturas-mitologia-001.json` → `editorial/lecturas-mitologia-001.json`, propuesta de
  `lesson_builder` sin aplicar): los Soles, cantos a los dioses, Quetzalcóatl deja Tollan, Huitzilopochtli guía a los mexicas.
* Unidad «Los nombres del calendario» (numerales 1–13 y signos), validada contra las tablas, Tlachia y los pasajes.
* Cola: `reports/entities-review-queue.json` (decisiones en `editorial/lesson-decisions.json`, misma huella que el resto).
  Nada se presenta como revisado sin revisor; los atributos de plantilla llevan la marca «Automático».

```bash
python3 -m nahuatl_local.entities
```

`--check` falla si algún archivo generado no está al día (`tests/test_entities.py` lo exige). Cambiar la semilla, el
índice de términos, `text.loose_key`, el catálogo de Tlachia o las lecturas publicadas ⇒ regenerar.
