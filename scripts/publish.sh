#!/usr/bin/env bash
# Releases are published only by .github/workflows/release.yml: push a protected
# tag vX.Y.Z and a second maintainer approves the "pypi" environment. There is
# no upload from a laptop (see SECURITY.md and MAINTAINERS.md).
echo "Releases are published only by .github/workflows/release.yml (tag vX.Y.Z)." >&2
exit 1
