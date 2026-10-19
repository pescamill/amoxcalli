#!/bin/bash
# Doble clic en macOS: arranca Amoxcalli y lo abre en el navegador.
cd "$(dirname "$0")" || exit 1
PY="$(command -v python3 || true)"
if [ -z "$PY" ] || ! "$PY" -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
  echo "Amoxcalli necesita Python 3.11 o más reciente: https://www.python.org/downloads/"
  read -r -n 1 -p "Pulsa una tecla para cerrar…"
  exit 1
fi
echo "Amoxcalli se abre en tu navegador (http://127.0.0.1:8766)."
echo "La primera vez prepara el análisis durante un minuto. Deja esta ventana abierta mientras lo usas; ciérrala para salir."
exec "$PY" -m nahuatl_local.platform serve --open
