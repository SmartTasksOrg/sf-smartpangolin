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

## Security problems

Security problems do not go here: see [SECURITY.md](SECURITY.md).

## Before you start

- For anything larger than a fix, open an issue first and say what you want
  to change and why.
- By contributing you agree that your contribution is licensed under the
  licence in [LICENSE](LICENSE). There is no separate contributor agreement.
- Be decent: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Rules every change keeps

1. No secrets, keys, tokens or personal data in the repository.
2. No new runtime dependency (see "Stdlib only at runtime" above).
3. Say what was tested and what was not. Do not write that something works
   on a platform or at a scale it was not run on.
4. Install lines name only packages listed with `"registered": true` in
   `names.json`; `python scripts/check_install_lines.py` enforces it in CI.
5. Add a line to [CHANGELOG.md](CHANGELOG.md) under "Unreleased".

## Dev setup

```bash
./scripts/bootstrap.sh          # .venv + editable install with dev extras
python -m pytest                # run the suite
ruff check src tests            # lint
python scripts/check_install_lines.py
```

## Changing the policy

Editing any rule changes `policy_sha256`, which is recorded in every manifest and
ledger entry — so a share can always be traced to the exact policy that produced
it. When you edit rules:

1. Bump `POLICY_VERSION` in `src/smartpangolin/engine.py`.
2. Add a test in `tests/test_pangolin.py` covering the new/changed rule.
3. Note it in `CHANGELOG.md` under a **Policy** subheading.

New content rules (`SEC-CONT-*`) must be **anchored** on a vendor prefix and a
fixed body length — match the token *format*, not "looks secret". That is what
keeps the policy low-noise and deterministic.

## Pull requests

- One logical change per PR.
- Tests pass and lint is clean.
- Update the relevant `docs/` page if behaviour changed.
