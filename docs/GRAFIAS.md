# Grafías: escribir como uno escribe y encontrar la palabra con sus fuentes

Una persona escribe una palabra como la escribiría (*kuali*, *kualli*, *qualli*, *cuali*, o con un error) y al
instante ve las posibilidades, con sus fuentes, aunque esa grafía exacta no exista en el archivo. Es la puerta de
entrada para hablantes de variedades modernas: **la herramienta relaciona, no impone un estándar.** Ninguna
grafía se presenta como «la correcta»; cada fuente conserva la suya y cada quien elige en qué perfil verla.

Código: `nahuatl_local/spelling.py` (perfiles, conversor, grafo, búsqueda), `spelling_mining.py` (minería y
compuerta), `spelling_evaluation.py` (medida). Interfaz: `platform_web/spelling.js`.

## Forma pivote

Para relacionar se usa una forma interna, nunca visible: la clave laxa (`text.loose_key`), que parte de la clave
fonémica del analizador y une la ortografía colonial con la moderna (k/c/qu, kw/cu/qu, w/hu/u, s/z/ç/c, ts/tz,
saltillo h/j, consonantes dobles). Todo lo demás (reglas de perfil, distancia, grafo) trabaja sobre ella.

## Perfiles ortográficos y conversor

| Perfil | Rasgos |
|---|---|
| Colonial (Molina, Carochi) | c/qu, qu/cu + vocal, uc en coda, hu/uh, z/c, tz, tl, ch, x; sin saltillo ni vocales largas |
| ACK (Andrews, Campbell, Karttunen) | c/qu, cu/uc, hu/uh, z/c, tz; saltillo h; macrón solo si un diccionario lo registra |
| SEP / INALI | k, kw, w, s, ts, ch, tl, x; saltillo h |
| Rasgos del archivo por variedad | **medidos** en Axolotl: cómo escribe cada variedad kw, w, s, ts, el saltillo, -tl y las consonantes dobles (Sierra de Puebla: *kuali*, *metsti*; Huasteca occidental: *kuali*; Huasteca oriental: *cuali*; Morelos y central: *cualli*) |

Límite que la pantalla dice siempre: **las fuentes coloniales casi nunca marcan vocales largas ni saltillo**; una
forma colonial convertida a ACK o SEP no puede recuperarlos. Solo aparecen si la grafía de partida los trae.

## Búsqueda tolerante (`Search.search`, `/api/spellings?q=`)

Para cualquier entrada, candidatos por:

1. **pivote igual** (otra convención ortográfica: confianza alta);
2. **reglas de perfil** (`RULES`): u tras vocal = w en coda (*kuautli* → *cuauhtli*), -t final = -tl, z/s ante
   consonante = tz, s/sh = x, x = ch, e = i, y entre i y vocal, n = m ante p, tl = t dentro de la palabra;
3. **distancia de edición ponderada** sobre el pivote: las sustituciones ortográficas conocidas cuestan poco
   (0,3–0,5), un error arbitrario cuesta 1; índice de borrados para responder en milisegundos;
4. **raíz del analizador** para formas flexionadas.

Cada grafía lleva a su palabra (entrada del diccionario o grupo del archivo) y la lista se ordena por costo y
evidencia: apariciones en el archivo (con variedades y un pasaje de ejemplo), entradas del diccionario y glifos.
Cada candidato dice por qué se propone y con qué confianza. Si lo escrito no está atestiguado, la respuesta lo
dice y solo propone grafías atestiguadas: una conjetura nunca se presenta como forma del archivo.

## Grafo de equivalencias (`Graph`)

Nodos: claves pivote atestiguadas, cada una con sus grafías originales. Aristas con tipo y evidencia: **regla de
perfil**, **traducciones alineadas que coinciden** (una palabra española distintiva común en los pasajes de
ambas), **par minado** y **confirmación humana**. Solo las aristas seguras forman grupos; el índice de términos
(`terms.py`) toma sus grupos de este grafo y muestra las aristas inciertas aparte, como los homógrafos. Una
arista es segura si la confirma un editor, si su regla está activa, o si su regla está en revisión pero las
traducciones la confirman (política `aligned`, también sometida a la compuerta). Si las traducciones se
contradicen, la arista queda incierta.

## Minería con revisión (`python -m nahuatl_local.spelling_mining`)

Propone reglas desde pares cercanos con traducciones que coinciden (la diferencia de símbolos agregada por
variedad). **Una regla solo se activa si mejora la partición dev del conjunto congelado sin bajar la precisión
ni añadir uniones erróneas**, y si a lo sumo el 25 % de sus aristas contradice las traducciones; más del 50 %
la descarta. Lo demás queda en revisión: aparece como incierto y en la cola de editores. Resultado vigente
(`configs/spelling-rules-v1.json`): activas `final_tl`, `z_tz` y `aligned`; las reglas minadas (a = o en la
Sierra de Puebla, k = λ…) no pasaron la compuerta.

Revisión humana: en la vista «Grafías», con el modo editor y una sesión, cada asociación tiene *Confirmar*,
*Separar* y *Deshacer* (`POST /api/spellings/review`). Las decisiones se añaden a
`editorial/spelling-review.json` con quién y cuándo; la última por par manda y *Deshacer* la retira.

## Medida

`evaluation/spelling-search-v1.json` (111 consultas, 54 pares; escrito y congelado antes de construir, commit
c079a11). Informe: sección «Grafías» de [reports/EVALUACION.md](../reports/EVALUACION.md) (`make eval`).

| | Top-1 | Top-3 | Precisión del grafo | Cobertura del grafo |
|---|---|---|---|---|
| dev (42) | 90,5 % | 97,6 % | 100 % | 86,7 % |
| test (69) | 94,2 % | 97,1 % | 100 % | 81,5 % |

Sin reglas activas (pivote, reglas solo como candidatos, distancia y raíz): dev 88,1 % / 97,6 %, cobertura del
grafo 66,7 % (78,6 % de top-1 con el primer peso de la evidencia, 0,12, cambiado a 0,2 mirando solo dev). En el
índice de términos (`term-groups-v1`), consulta → grupo pasa de 90,3 % a 94,4 % y «mismo grupo» de 66,7 % a
81,0 %; morfología y Preguntar no cambian.
Latencia con índices construidos: mediana 0,5 ms, máximo ~1,5 ms por consulta. Construcción del grafo: ~1,6 s
sobre el índice de términos.

Fallos conocidos de la tarea: *kuautli*, *mestli*/*meztli*/*metztli*, *sochitl*, *xochit* y las grafías de
*Huitzilopochtli* llevan a su palabra. Quedan explicados:

- *ilhuicac*: el diccionario tiene su propia entrada (Wiktionary, «en el cielo»), que va primero; *ilhuicatl*
  aparece segunda por la raíz del analizador.
- *tonatih*, *uizilopochtli*: son grafías atestiguadas (una aparición) y se muestran primero como lo que son;
  la palabra frecuente va segunda.
- *kuouit* (Sierra de Puebla, *cuahuitl*): necesita a = o, que la minería propuso pero no pasó la compuerta.
- *ejekatl*: la clave laxa conserva la vocal doble tras quitar la j (*eekat*); arreglarlo es cambiar
  `text.loose_key`, entrada medida de otras evaluaciones.
- *tlalticpac*: el catálogo léxico registra *tlalticpac* como grafía de la entrada *tlalli*.
