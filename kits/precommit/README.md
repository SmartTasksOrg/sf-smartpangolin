# pre-commit (https://pre-commit.com)
```yaml
repos:
  - repo: https://github.com/SmartTasksOrg/sf-smartpangolin
    rev: v1.0.0
    hooks:
      - id: pangolin-guard
```
Override false positives per-repo in `.pangolin.json` (`allow: [...]`); every override is auditable.
