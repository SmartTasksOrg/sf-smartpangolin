# Contributing to SmartPangolin

Thanks for helping make code-sharing safe by default.

## Ground rules

- **Stdlib only at runtime.** SmartPangolin must install and run with zero
  third-party dependencies. Dev tooling (pytest, build, twine, ruff) is fine.
- **Fail closed.** New rules default to excluding. A false positive is a visible
  line in `EXCLUSIONS.json` and one `allow` entry to clear; a false negative is
  a leaked secret. We optimise for the former.
- **No redaction.** Never rewrite file contents. Files ship whole or not at all.
- **Determinism is a feature.** Any change that makes two runs over an unchanged
  tree diverge (in `content_sha256`, not `zip_sha256`) is a bug.

## Dev setup

```bash
./scripts/bootstrap.sh          # .venv + editable install with dev extras
python -m pytest                # run the suite
ruff check src tests            # lint
```

## Changing the policy

Editing any rule changes `policy_sha256`, which is recorded in every manifest and
ledger entry — so a share can always be traced to the exact policy that produced
it. When you edit rules:

1. Bump `POLICY_VERSION` in `src/pango/engine.py`.
2. Add a test in `tests/test_pangolin.py` covering the new/changed rule.
3. Note it in `CHANGELOG.md` under a **Policy** subheading.

New content rules (`SEC-CONT-*`) must be **anchored** on a vendor prefix and a
fixed body length — match the token *format*, not "looks secret". That is what
keeps the policy low-noise and deterministic.

## Pull requests

- One logical change per PR.
- Tests pass and lint is clean.
- Update the relevant `docs/` page if behaviour changed.
