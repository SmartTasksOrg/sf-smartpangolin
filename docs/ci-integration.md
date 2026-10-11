# CI integration

SmartPangolin is meant to be *engrained* in a pipeline, not run by hand.

## Pre-commit (block the leak before it's committed)

Add to `.pre-commit-config.yaml` (see `examples/pre-commit-config.example.yaml`):

```yaml
repos:
  - repo: https://github.com/SmartTasksOrg/sf-smartpangolin
    rev: v3.0.0
    hooks:
      - id: pangolin-guard
```

Then `pre-commit install`. The hook runs a `--dry-run --share public` seal and
surfaces any secret-class exclusion before the commit lands.

## GitHub Actions — PR guard

Use the reusable composite action (`adapters/github-action/action.yml`):

```yaml
name: sf-smartpangolin
on: [pull_request]
jobs:
  guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1, read 2026-10-08
      - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97  # v7.0.0, read 2026-10-08
        with: { python-version: "3.12" }
      - uses: SmartTasksOrg/sf-smartpangolin/adapters/github-action@v3.0.0
        with:
          root: .
          share: public
```

It fails the PR if a *tracked* file trips a `SEC-PATH-*`, `SEC-CONT-*`, or
`SEC-DIR-*` rule — i.e. a secret is on its way into history.

## GitLab CI

```yaml
sf-smartpangolin:
  image: python:3.12-slim
  script:
    # published only by SmartTasksOrg/sf-smartpangolin, with provenance; pin the version you reviewed
    - python -m pip install "sf-smartpangolin==3.0.0"
    - sf-smartpangolin pack --root . --share public --dry-run --debug
```

## Producing a sealed context artifact on release

```yaml
# published only by SmartTasksOrg/sf-smartpangolin, with provenance; pin the version you reviewed
- run: python -m pip install "sf-smartpangolin==3.0.0"
- run: sf-smartpangolin pack --root . --share public
- uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a  # v7.0.1, read 2026-10-08
  with:
    name: sealed-context
    path: ../extracted_source/share_archive/*.zip
```

Downstream jobs (or a human) can `sf-smartpangolin verify` the artifact, and compare its
`content_sha256` across builds to confirm the shared payload didn't change.
