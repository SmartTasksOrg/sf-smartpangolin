#!/usr/bin/env bash
# Validate and upload to PyPI (or TestPyPI with --test).
# Auth: set TWINE_USERNAME=__token__ and TWINE_PASSWORD=<pypi-token>, or use ~/.pypirc.
set -euo pipefail
cd "$(dirname "$0")/.."

REPO_ARG=()
if [ "${1:-}" = "--test" ]; then
  REPO_ARG=(--repository testpypi)
  echo "[publish] target: TestPyPI"
else
  echo "[publish] target: PyPI"
fi

python -m pip install --upgrade build twine >/dev/null
./scripts/build.sh
echo "[publish] twine check"
python -m twine check dist/*
echo "[publish] uploading"
python -m twine upload "${REPO_ARG[@]}" dist/*
echo "[publish] done"
