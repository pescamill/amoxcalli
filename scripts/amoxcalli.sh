#!/usr/bin/env bash
# Arranque único de Amoxcalli: un proceso sirve la aplicación, Voces (/aportar) y la API.
#   bash scripts/amoxcalli.sh serve [opciones]   solo biblioteca estándar de Python
#   bash scripts/amoxcalli.sh setup [opciones]   prepara .venv, dependencias y pesos del modelo local; después sirve
# Opciones (ambos): --host --port --db --public-origin --disable-model --adapter --explain-model claude
# Detalle: python3 -m nahuatl_local.platform serve --help
set -euo pipefail
cd "$(dirname "$0")/.."

usage() {
  sed -n '2,6s/^# \{0,1\}//p' "$0" >&2
  exit "$1"
}
COMMAND="${1:-}"
[ $# -gt 0 ] && shift
case "$COMMAND" in
  serve|setup) ;;
  -h|--help|help) usage 0 ;;
  *) usage 2 ;;
esac

# Un servidor anterior en el mismo puerto sirve código viejo y confunde el navegador.
PORT=8766
EXPECT_PORT=0
for arg in "$@"; do
  if [ "$EXPECT_PORT" = 1 ]; then PORT="$arg"; EXPECT_PORT=0; continue; fi
  case "$arg" in --port) EXPECT_PORT=1 ;; --port=*) PORT="${arg#--port=}" ;; esac
done
if [ "$EXPECT_PORT" = 1 ] || ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
  echo 'Usa --port con un entero entre 1 y 65535.' >&2
  exit 2
fi

if [ "$COMMAND" = setup ]; then
  if [ ! -x .venv/bin/python ]; then "${NAHUATL_PYTHON:-python3}" -m venv .venv; fi
  if ! .venv/bin/python -c 'import torch,transformers,peft' >/dev/null 2>&1; then
    if [ "$(uname -s)" = Linux ]; then .venv/bin/python -m pip install 'torch==2.7.1' --index-url https://download.pytorch.org/whl/cpu; fi
    .venv/bin/python -m pip install -r requirements.txt
  fi
  .venv/bin/python -m nahuatl_local.download --only model
  PYTHON=.venv/bin/python
elif [ -n "${NAHUATL_PYTHON:-}" ]; then PYTHON="$NAHUATL_PYTHON"
elif [ -x .venv/bin/python ]; then PYTHON=.venv/bin/python
else PYTHON=python3; fi

if command -v lsof >/dev/null 2>&1; then
  # Nunca incluye clientes (por ejemplo, el navegador conectado al servidor).
  PIDS="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "$PIDS" ]; then
    echo "Deteniendo servidor previo en el puerto $PORT: $PIDS"
    kill $PIDS 2>/dev/null || true
    sleep 1
    PIDS="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
    [ -n "$PIDS" ] && kill -9 $PIDS 2>/dev/null || true
  fi
fi
# --db es opción global del módulo: va antes del subcomando.
ARGS=()
DB=()
while [ $# -gt 0 ]; do
  case "$1" in
    --db) DB=(--db "${2:?--db requiere una ruta}"); shift 2 ;;
    --db=*) DB=(--db "${1#--db=}"); shift ;;
    *) ARGS+=("$1"); shift ;;
  esac
done
exec "$PYTHON" -m nahuatl_local.platform ${DB[@]+"${DB[@]}"} serve ${ARGS[@]+"${ARGS[@]}"}
