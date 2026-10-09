# SmartPangolin documentation

- **[design.md](design.md)** — the five commitments and the failure they close.
- **[policy.md](policy.md)** — full rule reference and how to tune it.
- **[secret-folder-standard.md](secret-folder-standard.md)** — the `.secret/` convention and `.pangolin.json` overrides.
- **[cli.md](cli.md)** — every subcommand and flag.
- **[ci-integration.md](ci-integration.md)** — pre-commit, GitHub Actions, GitLab CI.
- **[porting.md](porting.md)** — the conformance contract for Go / Java / Node ports.
- **[ecosystem.md](ecosystem.md)** — where SmartPangolin sits in the SmartTasks / IAIso work.
- **[faq.md](faq.md)** — common questions.

## 30-second tour

SmartPangolin is not on PyPI yet; install from a clone (README, "Install").

```bash
git clone https://github.com/SmartTasksOrg/sf-smartpangolin
cd sf-smartpangolin
python -m venv .venv
. .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install .
sf-smartpangolin init --root .                      # scaffold the .secret standard
sf-smartpangolin pack --root . --share public       # seal for a third party
sf-smartpangolin verify <zip>                        # prove integrity
sf-smartpangolin triage <zip> --git                  # what did git track that didn't ship?
```

SmartPangolin is stdlib-only (Python 3.8+, zero runtime dependencies) and every share
comes with a manifest, an exclusion audit, the exact policy that ran, and a
`content_sha256` you can compare across runs.
