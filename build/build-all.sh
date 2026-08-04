#!/usr/bin/env bash
# Build every SmartPangolin package from source. Requires the toolchains you use.
set -uo pipefail
cd "$(dirname "$0")/.."
echo "== spec sync (single source of truth) =="; python3 tools/export_policy.py
echo "== PyPI (python) =="; python3 -m build && python3 -m twine check dist/*
echo "== Node port =="; ( cd ports/node && npm pack )
echo "== Go port =="; ( cd ports/go && go build -o pangolin-check . && echo "  built ports/go/pangolin-check" )
echo "== Java port =="; ( cd ports/java && mkdir -p out && javac -d out src/*.java && \
    printf 'Main-Class: Main\n' > out/manifest.txt && jar cfm pangolin-check.jar out/manifest.txt -C out . && echo "  built ports/java/pangolin-check.jar" )
echo "== PHP port =="; php -l ports/php/pangolin-check.php
echo "== conformance gate =="; bash ports/conformance/run.sh
echo "ALL BUILDS DONE"
