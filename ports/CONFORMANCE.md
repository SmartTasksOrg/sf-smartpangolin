# Conformance & honest limitations

`conformance/run.sh` builds a fixture (`conformance/fixture.py`) that exercises
**every** rule — all 21 `SEC-CONT-*`, 9 `LOC-*`, 11 `SEC-PATH-*`, plus PII samples and gitignore
(basename, anchored, directory, negation, `**`), the allowlist, and clean files —
then asserts Node, Go, Java and PHP each emit the **same rule ID per file as the
Python engine**, in `public`, `private`, and `--pii` modes.

```
ALL PORTS CONFORMANT (incl. PII)  # node/go/java/php
```

## What the ports intentionally do NOT do (use the Python tool for these)
- **Sealing.** Ports classify; they do not build the share zip, the signed
  manifest, the two hashes, or the audit ledger. `pango` is the reference for the
  actual artifact.
- **Operational rules.** Ports skip `OPS-OVERSIZE` (huge files) and the
  binary-safe-extension allowance. Ports are **fail-closed on binaries**: any file
  with a NUL byte in the first 8 KB is `OPS-BINARY`. This can differ from Python,
  which may *include* a known-binary extension. Safer, but not identical — run the
  Python tool when you intend to ship binary assets.

## Parity notes
- Go uses RE2 (no lookahead); the two lookahead rules (`SEC-CONT-OPENAI`,
  `LOC-NIXUSER`) use a base pattern + a code post-filter, verified against Python.
- `\b` is ASCII in RE2/PCRE/JS/Java and Unicode-aware in Python `re`; for the
  ASCII token patterns here this does not diverge.
- Exit code: every port exits non-zero **iff** a `SEC-*` finding is present, so all
  four fail CI identically. `LOC-*`/`OPS-*` are informational.
- Regenerate + re-sync every port from the engine with
  `python3 tools/export_policy.py`, then re-run the gate.
