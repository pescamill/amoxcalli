#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then "${NAHUATL_PYTHON:-python3}" -m venv .venv; fi
if ! .venv/bin/python -c 'import torch,transformers,peft' >/dev/null 2>&1; then
  if [ "$(uname -s)" = Linux ]; then .venv/bin/python -m pip install 'torch==2.7.1' --index-url https://download.pytorch.org/whl/cpu; fi
  .venv/bin/python -m pip install -r requirements.txt
fi
.venv/bin/python -m nahuatl_local.download --only model
exec .venv/bin/python -m nahuatl_local.platform serve "$@"
