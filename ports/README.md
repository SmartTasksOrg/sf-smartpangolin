# SmartPangolin ports — the policy is the contract

The Python package (`pango`) is the reference implementation. These are **native,
dependency-free ports** for teams that live in other ecosystems and want a
pre-publish / CI gate without a Python runtime.

They do **not** re-invent the ruleset. `spec/policy.json` is exported from the
Python engine (`tools/export_policy.py`) and every port loads *that same spec*:

```
src/smartpangolin/engine.py  ──export──▶  spec/policy.json
                                              │
                 ┌────────────────────────────┼────────────────────────────┐
        ports/node   ports/go   ports/java   ports/php
     (each loads the same spec)
```

A port is **conformant** when, given the same tree, it emits the same rule ID for
every file as the Python engine. `ports/conformance/run.sh` proves it in both
`public` and `private` modes:

```
$ bash ports/conformance/run.sh
== mode=public ==
  node   OK (11 files)
  go     OK (11 files)
  java   OK (11 files)
== mode=private ==
  ...
ALL PORTS CONFORMANT
```

Every rule is exercised (see `ports/CONFORMANCE.md` for scope and honest limitations).

Scope: the ports cover the security contract — path/filename rules, in-content
secret patterns, LOC (local-infra, public-mode only), the allowlist, and
`.gitignore` honouring (`OPS-GITIGNORE`). The full Python tool remains the
reference for zip sealing, the manifest, hashes, and the audit ledger.

**Never ship a secret scanner to the browser.** For a React app the integration
is a CI / pre-publish check (see `ports/node`), not in-page scanning.
