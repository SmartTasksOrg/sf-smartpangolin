#!/usr/bin/env bash
# Create a local venv and install SmartPangolin (dev extras). Idempotent.
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
VENV="${VENV_DIR:-.venv}"

if [ ! -d "$VENV" ]; then
  echo "[bootstrap] creating venv at $VENV"
  "$PY" -m venv "$VENV"
fi

# shellcheck disable=SC1090
source "$VENV/bin/activate"
python -m pip install --upgrade pip >/dev/null
echo "[bootstrap] installing SmartPangolin (editable, dev extras)"
pip install -e ".[dev]"

echo
echo "[bootstrap] done. Activate with:  source $VENV/bin/activate"
sf-smartpangolin --version
