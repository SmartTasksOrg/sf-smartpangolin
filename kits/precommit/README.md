# pre-commit (https://pre-commit.com)
```yaml
repos:
  - repo: https://github.com/SmartTasksOrg/sf-smartpangolin
    rev: v3.0.0  # the tag v3.0.0 exists only after the first release
    hooks:
      - id: pangolin-guard
```
Override false positives per-repo in `.pangolin.json` (`allow: [...]`); every override is auditable.
