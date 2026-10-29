# Aclaraciones

Una sola forma de decir «esto no cuadra» desde cualquier pasaje, palabra o ficha de Amoxcalli.

## Para quien lee

1. Toca **Aclarar o corregir** junto al pasaje.
2. Elige qué pasa (obligatorio, un toque): traducción, análisis, grafía, fuente, uso en una variante actual o duda.
3. Si quieres: una frase, una propuesta y cómo lo sabes (fuente con página, hablante de una variante, estudio, o «no
   estoy seguro»).
4. **Guardar**: queda en `data/community/aclaraciones.jsonl` de tu instalación, con el ID, el texto que viste, la
   ruta y la versión. Nada sale de tu computadora.
5. **Compartir** (si quieres): «Enviar por GitHub» abre un issue ya escrito; «Copiar» sirve para correo o mensaje.
   En *Más → Mis aclaraciones* puedes verlas, descargarlas en JSON o borrarlas.

No se piden nombre, correo ni ubicación. La variante se guarda solo si dices que hablas una variante actual, y como
tú la nombras.

## Para quien revisa

Cada aclaración compartida lleva un bloque JSON tras la marca `<!-- amoxcalli:aclaracion -->`. El flujo
`.github/workflows/aclaraciones.yml` la ordena sola al abrirse el issue:

- comprueba que el ID exista en el corpus (si no, etiqueta `id-no-encontrado`);
- etiqueta por categoría (`traducción`, `análisis`, `grafía`, `fuente`, `uso actual`, `duda`) y `variante-actual`
  cuando viene de una persona hablante;
- comenta con una tabla: registro actual junto a lo que vio la persona, su propuesta y su cita;
- avisa si hay issues abiertos sobre el mismo ID.

No corrige nada. Una persona coteja con la fuente; si se confirma, corrige el registro y cierra el issue con el
commit. Si toca una variante actual, la revisan hablantes de esa variante.

Las aclaraciones que llegan por correo (texto copiado o el `.json` descargado) se leen igual:

```bash
python3 -m nahuatl_local.aclaraciones triage archivo.json
```
