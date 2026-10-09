# The `.secret` folder standard

A small, enforceable convention so "where do secrets live" becomes repo
structure instead of a per-developer habit.

## The rule

Any directory named `.secret` or `.secrets` is matched by rule `SEC-DIR-SECRET`
and is **never shipped, in any mode** — public or private. It is pruned during
the walk, so its contents never even become candidates. There is no pattern to
slip past and no scan to fool: put a real credential under `.secret/` and it is
structurally impossible to include it in a share.

## Layout

```
your-repo/
├── .secret/
│   ├── .gitignore        # "*" — so the remote never sees these either
│   ├── prod.env
│   ├── service-account.json
│   └── signing.key
├── .pangolin.json      # per-repo overrides (optional)
├── .env.example          # templates ship (allowlisted)
└── src/...
```

Scaffold it:

```bash
sf-smartpangolin init --root .
```

`init` creates `.secret/` with a `*`-ignoring `.gitignore` and writes a starter
`.pangolin.json`. Because `.secret/` is both git-ignored and never-shipped, a
secret placed there is protected at *both* boundaries: it won't reach your git
remote, and it won't reach a share.

## `.pangolin.json` — per-repo overrides

The embedded policy can't know your repo. This file adjusts it, and **every field
folds into `policy_sha256`**, so a share built with overrides is cryptographically
distinguishable from one built without — no silent bypass.

| Field | Type | Effect |
|---|---|---|
| `share_mode` | `"public"`/`"private"` | default mode when `--share` is omitted |
| `source_only` | bool | restrict to recognised source extensions |
| `max_chars` | int | per-shard character ceiling |
| `allow` | `[relpath]` | force-include despite a rule (recorded as an override) |
| `deny_globs` | `[glob]` | extra path exclusions → rule `SEC-PATH-USER` |
| `exclude_folders` | `[name]` | extra folder names to skip |
| `exclude_paths` | `[relpath]` | subtrees to skip |

`allow` is the escape hatch for false positives — each entry names one file, and
each override is written into the manifest and the ledger next to the rule it
overrode. There is deliberately **no `--allow-all`**.
