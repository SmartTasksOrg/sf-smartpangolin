# Changelog

All notable changes to SmartPangolin are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versioning is semantic.

## Unreleased

### Security
- Install instructions no longer name packages the maintainers have not
  published. Until the first release, install from a clone (README, "Install").
- New `SECURITY.md` (private vulnerability reporting), `names.json` (the only
  official package names) and a CI check that fails when a document names any
  other package.
- Releases are built and published only by `.github/workflows/release.yml`
  through PyPI trusted publishing, with provenance attestations.

### Changed
- **Renamed (breaking), `sf-` = Smart Family:** repository `SmartTasksOrg/sf-smartpangolin`, PyPI package `sf-smartpangolin`, command `sf-smartpangolin`, import package `sf_smartpangolin`, MCP server `io.github.smarttasksorg/sf-smartpangolin`. The unprefixed names are not used any more, so nobody can be sent to a look-alike.
- README: "Install" and "Status" sections (Status: experimental, no "production" claim); MCP marker is the bare server name.
- `pyproject.toml`: "3 - Alpha" classifier (was "5 - Production/Stable"), licence files incl. NOTICE, URLs point at `master`.
- Token uploads removed: `make publish`, `make publish-test` and `scripts/publish.sh` no longer upload; `PUBLISHING.md` rewritten.
- Docs refer to tag `v3.0.0` (the first release) instead of `v1.0.0`/`v1`, which do not exist.
- Node port package `sf-smartpangolin-check` (unpublished); Go module path `github.com/SmartTasksOrg/sf-smartpangolin/ports/go`.
- `MARKETING.md` moved out of the public repository.

## [3.0.0] — 2026-08-04

Aligned to the **Smart\* family v3.0.0** release. The full packager (`pango`
`pack`/`verify`/`triage`, engine, PII, ports, kits, adapters, docs) is unchanged
and intact. Additions for family integration:

- Family quick-scan API — `smartpangolin.core.scan()` and `smartpangolin.models`
  (`ScanResult`, `Finding`) — with **base64/hex-decode-aware** secret detection and
  a **deterministic, real SHA-256** `policy_hash`.
- Bundled `demo/repo`, IAIso mapping (`spec/iaiso-map.json`), `.smart.json` family
  metadata, and a `smartpangolin` console alias (the `pango` command is unchanged).
- `pango`/`smartpangolin` (no args) and `--demo` now run a safe demo instead of
  packing the current directory.

## [1.0.0] — 2026-08-02

First public release. Extracted and hardened from the SmartTasks internal
`get_folder_structure.py -> get_source.py -> get_share_zip.py` pipeline.

### Added
- `pango` CLI (`pack`, `verify`, `triage`, `tree`, `purge`, `policy`, `init`) and
  a Python API `smartpangolin.pack()` returning a structured `PackResult`.
- Rule families with stable, greppable IDs recorded in `EXCLUSIONS.json`:
  `SEC-PATH-*` (dangerous filenames), `SEC-CONT-*` (~20 in-content secret
  patterns), `LOC-*` (local-infrastructure leaks), `OPS-*` (operational).
- `.gitignore` honouring (`OPS-GITIGNORE`) — nested files, negation, anchored and
  directory patterns, `**`; on by default, overridable and auditable.
- `public` / `private` share modes (local-infrastructure disclosure toggle).
- The `.secret/` folder standard (`SEC-DIR-SECRET`) and per-repo `.pangolin.json`
  overrides that fold into an auditable `policy_sha256`; deterministic
  `content_sha256` and byte-reproducible archives.
- Native, dependency-free ports for **Node, Go, Java, and PHP**, each conformance-
  tested to produce the same rule IDs as the Python reference on every rule and
  both share modes (`ports/conformance/run.sh`).
- Integration kits: a zero-dependency **MCP server** (`smartpangolin-mcp`) for AI
  coding tools, plus LangChain / LlamaIndex / function-calling adapters and
  CI / pre-commit templates.
- Editor secret-search patterns for VS Code and ripgrep, and a one-command
  bootstrap for the standardized secret locations.
- Hardening: secrets embedded in binary-safe assets (images, fonts) and in
  oversize files are now scanned and withheld, and zero-width / invisible
  characters are stripped before matching (so a key split by a hidden character
  is still caught) — across Python and all four ports.

