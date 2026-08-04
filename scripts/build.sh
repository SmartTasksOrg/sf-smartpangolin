#!/usr/bin/env bash
# Build a clean sdist + wheel into dist/.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf build dist ./*.egg-info src/*.egg-info
python -m pip install --upgrade build >/dev/null
python -m build
echo "[build] artifacts:"
ls -la dist/
