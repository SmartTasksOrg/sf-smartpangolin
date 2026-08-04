# Changelog

All notable changes to SmartPangolin are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versioning is semantic.

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

