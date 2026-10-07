#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  training_python="${NAHUATL_PYTHON:-python3}"
  "$training_python" - <<'PY'
import sys
if sys.version_info[:2] not in [(3, 11), (3, 12)]:
    raise SystemExit('Se requiere Python 3.11 o 3.12. Usa NAHUATL_PYTHON=python3.12 bash scripts/autotrain.sh')
PY
  "$training_python" -m venv .venv
fi
if ! .venv/bin/python - <<'PY'
from importlib.metadata import version
from pathlib import Path
import sys
try:
    required = Path('requirements.txt').read_text().splitlines()
    for line in required:
        if '==' in line and not line.startswith('#'):
            name, expected = line.split('==', 1)
            assert version(name).split('+')[0] == expected
except (Exception, AssertionError):
    sys.exit(1)
PY
then
  if [ "$(uname -s)" = Linux ]; then
    .venv/bin/python -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu
  fi
  .venv/bin/python -m pip install -r requirements.txt
fi
exec .venv/bin/python -m nahuatl_local.autotrain --prepare "$@"
