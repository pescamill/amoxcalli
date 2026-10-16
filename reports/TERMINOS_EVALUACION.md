# Evaluación de grupos de término

Índice `terms-v1` · conjunto `term-groups-v1` · sin modelos. Regenerar: `python -m nahuatl_local.term_evaluation` (o `make reports`).

Escrito antes de construir el índice de términos y antes de mirar sus resultados. Las expectativas vienen del conocimiento de la lengua y de los datos de entrada (nombres de glifos del diccionario y designaciones de Tlachia), no de la salida del índice. dev: términos vistos durante la exploración (los siete de la tarea y atl); test: escritos sin consultar la variación del archivo. No se ajusta el conjunto después de medir; una corrección se publica como v2.

| Partición | Términos | Consulta → grupo (top-1) | Mismo grupo | Grafías (cualquier nivel) | Grafías seguras | Glifos | Precisión grafías* | Precisión glifos* | Homógrafos separados |
|---|---|---|---|---|---|---|---|---|---|
| dev | 7 | 96.7% de 30 | 85.7% | 100.0% | 96.4% | 100.0% | 100.0% | 100.0% | 100.0% |
| test | 14 | 85.7% de 42 | 57.1% | 95.5% | 86.4% | 100.0% | 100.0% | 100.0% | None% |
| all | 21 | 90.3% de 72 | 66.7% | 98.0% | 92.0% | 100.0% | 100.0% | 100.0% | 100.0% |

\* Precisión sobre lo etiquetado: aciertos seguros frente a formas o glifos que el conjunto marca como no seguros y el índice presenta como seguros.

## Por término

| Término | Partición | Grupo | Consultas | Grafías | Glifos | Faltan | Presentadas como seguras sin serlo |
|---|---|---|---|---|---|---|---|
| calli | dev | calli (dictionary) | 5/5 | 7/7 | 3/3 | — | — |
| cualli | dev | cualli (dictionary) | 5/5 | 6/6 | 0/0 | — | — |
| tonatiuh | dev | tonatiuh (dictionary) | 4/4 | 2/2 | 2/2 | — | — |
| coatl | dev | coatl (dictionary) | 5/5 | 4/4 | 3/3 | — | — |
| cihuatl | dev | cihuatl (dictionary) | 5/5 | 5/5 | 1/1 | — | — |
| xochitl | dev | xochitl (dictionary) | 3/4 | 3/3 | 3/3 | — | — |
| atl | dev | atl (dictionary) | 2/2 | 1/1 | 2/2 | — | — |
| tlacatl | test | tlacatl (dictionary) | 3/3 | 3/3 | 1/1 | — | — |
| tochtli | test | tochtli (dictionary) | 2/3 | 1/1 | 2/2 | — | — |
| itzcuintli | test | itzcuintli (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| ehecatl | test | eecatl (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| mazatl | test | mazatl (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| ocelotl | test | ocelotl (dictionary) | 2/3 | 1/1 | 2/2 | — | — |
| cuauhtli | test | cuauhtli (dictionary) | 3/4 | 2/2 | 2/2 | — | — |
| tecpatl | test | tecpatl (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| cipactli | test | cipactli (dictionary) | 2/2 | 1/1 | 2/2 | — | — |
| ozomatli | test | ozomahtli (dictionary) | 3/3 | 1/1 | 2/2 | — | — |
| teotl | test | teotl (dictionary) | 2/3 | 2/3 | 0/0 | teteo | — |
| tlalli | test | tlalli (dictionary) | 3/3 | 3/3 | 0/0 | — | — |
| ilhuicatl | test | ilhuicaātl (dictionary) | 2/3 | 2/2 | 0/0 | — | — |
| metztli | test | metztli (dictionary) | 2/3 | 1/1 | 1/1 | — | — |

Consultas que no llevan al grupo esperado:

- xochitl: «sochitl» → sin grupo (—)
- tochtli: «toxtli» → temoxtli (misma raíz (sin esta grafía en el archivo))
- ocelotl: «jaguar» → oceloquichtli (la acepción dice «jaguar»)
- cuauhtli: «kuautli» → sin grupo (—)
- teotl: «dios» → dios (grafía del archivo (sin entrada en el diccionario))
- ilhuicatl: «ilhuicac» → ilhuicac (misma palabra)
- metztli: «mestli» → meztli (grafía del archivo (sin entrada en el diccionario))
