#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
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
if [ -n "${NAHUATL_PYTHON:-}" ]; then exec "$NAHUATL_PYTHON" -m nahuatl_local.platform serve "$@";
elif [ -x .venv/bin/python ]; then exec .venv/bin/python -m nahuatl_local.platform serve "$@";
else exec python3 -m nahuatl_local.platform serve "$@"; fi
