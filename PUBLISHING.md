# Publishing

- Releases are published only by `.github/workflows/release.yml` (PyPI trusted publishing, provenance attestations), when a maintainer pushes a protected tag `vX.Y.Z` and a second maintainer approves the `pypi` environment.
- The PyPI name is `sf-smartpangolin` (`sf-` = Smart Family); the commands are `sf-smartpangolin` and `sf-smartpangolin-mcp`. Until the first release, install from a clone (README, "Install"); `pango` on PyPI is someone else's package.
- No other registry is published yet (npm `sf-smartpangolin-check`, Packagist, Maven Central: deferred). The names this project may use are listed in `names.json`.
- MCP server name: `io.github.smarttasksorg/sf-smartpangolin`. `publish/server.unpublished.json` becomes `server.json` only after the PyPI release is live and verified.
- There is no upload from a laptop: `make publish` and `scripts/publish.sh` stop with a message.
- The step-by-step release procedure is in the maintainers' runbook.
