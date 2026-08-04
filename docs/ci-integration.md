# CI integration

SmartPangolin is meant to be *engrained* in a pipeline, not run by hand.

## Pre-commit (block the leak before it's committed)

Add to `.pre-commit-config.yaml` (see `examples/pre-commit-config.example.yaml`):

```yaml
repos:
  - repo: https://github.com/SmartTasksOrg/smartpangolin
    rev: v1.0.0
    hooks:
      - id: pangolin-guard
```

Then `pre-commit install`. The hook runs a `--dry-run --share public` seal and
surfaces any secret-class exclusion before the commit lands.

## GitHub Actions — PR guard

Use the reusable composite action (`adapters/github-action/action.yml`):

```yaml
name: pango
on: [pull_request]
jobs:
  guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - uses: SmartTasksOrg/smartpangolin/adapters/github-action@v1
        with:
          root: .
          share: public
```

It fails the PR if a *tracked* file trips a `SEC-PATH-*`, `SEC-CONT-*`, or
`SEC-DIR-*` rule — i.e. a secret is on its way into history.

## GitLab CI

```yaml
pango:
  image: python:3.12-slim
  script:
    - pip install smartpangolin
    - pango pack --root . --share public --dry-run --debug
```

## Producing a sealed context artifact on release

```yaml
- run: pip install smartpangolin
- run: pango pack --root . --share public
- uses: actions/upload-artifact@v4
  with:
    name: sealed-context
    path: ../extracted_source/share_archive/*.zip
```

Downstream jobs (or a human) can `pango verify` the artifact, and compare its
`content_sha256` across builds to confirm the shared payload didn't change.
