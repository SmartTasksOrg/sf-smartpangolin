# Policy reference

The policy is a flat set of rules, each with a stable ID that appears verbatim in
`EXCLUSIONS.json`. Dump the live policy any time:

```bash
pango policy                 # full ruleset as JSON
pango policy --fingerprint   # just the sha256 (includes any .pangolin.json overrides)
```

## Families

| Prefix | What it matches | Public | Private |
|---|---|---|---|
| `SEC-PATH-*` | a filename/glob whose existence implies a credential | exclude | exclude |
| `SEC-DIR-*` | a directory name that holds credentials/metadata | exclude | exclude |
| `SEC-CONT-*` | an anchored credential *format* inside file content | exclude | exclude |
| `LOC-*` | local-infrastructure disclosure | exclude | **retain** |
| `OPS-*` | operational: unreadable/oversize/binary/undecodable/backup | exclude | exclude |
| `SEC-PATH-USER` | your `.pangolin.json` `deny_globs` | exclude | exclude |

## SEC-PATH (path/glob)

`.env` (and `*.env`, `.env.*`), `*.pem *.key *.p8 *.pkcs8 *.pkcs12`, keystores
(`*.pfx *.p12 *.jks *.keystore`), SSH keys (`id_rsa`, `*.ppk`, `authorized_keys`,
`known_hosts`), credential helpers (`.netrc`, `.git-credentials`, `.pypirc`,
`.npmrc`, `.dockercfg`), cloud service accounts (`credentials.json`,
`client_secret*.json`, `service-account*.json`), `kubeconfig`/`admin.conf`,
password vaults (`*.kdbx`, `*.gpg`, `.vault-token`), terraform state/vars
(`*.tfstate`, `*.tfvars`), shell history files, and database dumps
(`*.sql *.dump *.sqlite *.db`).

**Allowlist** (these win over the rules, so templates ship): `.env.example`,
`.env.sample`, `.env.template`, `env.example`.

## SEC-DIR (directory)

`.secret` / `.secrets` (the SmartPangolin standard), `.ssh .gnupg .aws .azure .kube
.docker`, `.git .svn .hg`, and build/vendor dirs (`node_modules`,
`__pycache__`, `.venv`, `dist`, `build`, `site-packages`, `.terraform`, …). Any
`venv_*`, `*_venv`, `*-venv` directory is also treated as a virtualenv.

## SEC-CONT (content)

Anchored, vendor-specific patterns — they match the token *format*, not "looks
secret": HuggingFace `hf_…`, AWS access keys and secret keys, GitHub PATs
(classic + fine-grained), GitLab PATs, **Anthropic `sk-ant-…` (checked before
OpenAI, since the prefix is a subset)**, OpenAI `sk-…`, Slack, Google, Stripe,
npm, PyPI upload tokens, Telegram, SendGrid, inline PEM/PuTTY private keys, JWTs,
docker auth blocks, and connection strings with inline passwords.

`SEC-CONT-ASSIGN` is the one deliberately broad rule: it fires on any
secret-named variable (`api_key`, `password`, `access_token`, …) assigned a
quoted literal of 8+ characters. It will occasionally catch something harmless
like a doc snippet — that is fail-closed working as intended. Clear it with a
single `allow` entry.

## LOC (local infrastructure) — public only

RFC1918 IPs (`10.* 192.168.* 172.16–31.*`), CGNAT/tailnet (`100.64–127.*`), IPv6
ULA (`fd..`), UNC paths (`\\host\share`), Windows user paths
(`C:\Users\name`), POSIX home dirs with a username, internal hostnames
(`*.local *.lan *.internal *.corp …`), MAC addresses, and SSH `HostName` lines.

**`127.0.0.1` and `localhost` are intentionally NOT rules.** They disclose
nothing about your network, and excluding them would drop nearly every server
script.

## OPS (operational, fail-closed)

`OPS-OVERSIZE` (> 8 MB, unscanned), `OPS-BINARY` (NUL byte in first 8 KiB),
`OPS-UNREADABLE`, `OPS-UNDECODABLE`, `OPS-STAT` (can't stat — on Windows usually
a >260-char path, flagged explicitly), `OPS-BACKUP` (`.bak`, `~`, `~$`).
`BINARY_SAFE_EXTS` (images, fonts) survive the binary check so you can ship a
logo or a `.woff`.

## Tuning for your repo

Rules live at the top of `src/pango/engine.py` as flat lists of
`(id, pattern, description)`. Editing one changes `policy_sha256` — recorded in
every manifest and ledger entry — so you can always tell which policy produced a
given share. **Bump `POLICY_VERSION` when you edit**, and add a test.

Common adjustments:

- **`SEC-PATH-DBDUMP`** globs `*.sql`. In an app repo full of SQL migrations this
  over-fires. Check with `pango triage <zip> SEC-PATH-DBDUMP --ext`; if it is
  mostly `.sql`, drop that glob (or `allow` the migration dir).
- **`LOC-NIXUSER`** skips `runner`, `user`, `ubuntu` as generic CI usernames. Add
  your own non-sensitive service accounts.
- **`BINARY_SAFE_EXTS`** — add any binary you genuinely need to ship.
- **`MAX_SCAN_BYTES`** (8 MB) drives `OPS-OVERSIZE`.

Prefer *not* to edit the shipped rules for one-off repo needs — reach for
`.pangolin.json` (`deny_globs`, `allow`, `exclude_folders`) first. It keeps the
core policy stable and still shows up in the fingerprint.

## OPS-GITIGNORE — the project's own ignore rules

By default SmartPangolin honours the repository's `.gitignore` (including nested
ignore files, `!` negation, anchored `/`, directory-only `dir/`, and `**`).
Anything git already ignores is excluded and reported under `OPS-GITIGNORE`.

Controls:
- `pango pack --no-gitignore` — ignore the ignore file.
- `.pangolin.json`: `"respect_gitignore": false` to disable; `"ignore_files":
  [".dockerignore"]` to honour additional ignore files.
- Force a specific ignored file back in with `allow`; it is recorded as an
  override and the decision is reflected in `policy_sha256`.
