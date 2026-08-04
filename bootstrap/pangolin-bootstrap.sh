#!/usr/bin/env bash
# Scaffold the SmartPangolin standardized secret locations in the current repo.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
echo "Bootstrapping SmartPangolin safe-zone in $(pwd) ..."
mkdir -p .secret/local .secret/ci .secret/data
[ -f .secret/README.md ] || cp "$here/templates/secret-README.md" .secret/README.md
[ -f .pangolin.json ]   || cp "$here/templates/pangolin.json" .pangolin.json
touch .gitignore
if ! grep -q "SmartPangolin standardized secret locations" .gitignore; then
  cat "$here/templates/gitignore-additions.txt" >> .gitignore
  echo "  + appended secret locations to .gitignore"
fi
echo "  + created .secret/{local,ci,data} and .pangolin.json"
echo "Done. Move sensitive files into .secret/ and run:  pango pack --dry-run"
