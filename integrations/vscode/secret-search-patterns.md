# Find secrets in your editor — patterns from SmartPangolin

These are the exact regexes SmartPangolin uses, ready to paste into the
**VS Code search box** (toggle **.\*** regex mode) or `ripgrep`. Standard naming,
so the same names line up with `.pangolin.json` overrides.

## In-content secrets (VS Code regex search)

| Rule | Regex |
|------|-------|
| `SEC-CONT-HF` | `\bhf_[A-Za-z0-9]{34}\b` |
| `SEC-CONT-AWSKEY` | `\b(?:AKIA\|ASIA\|ABIA\|ACCA)[0-9A-Z]{16}\b` |
| `SEC-CONT-AWSSEC` | `(?i)aws_secret_access_key\s*[=:]\s*[\"']?[A-Za-z0-9/+=]{40}` |
| `SEC-CONT-GHPAT` | `\bgh[pousr]_[A-Za-z0-9]{36}\b` |
| `SEC-CONT-GHFINE` | `\bgithub_pat_[A-Za-z0-9_]{60,}\b` |
| `SEC-CONT-GITLAB` | `\bglpat-[A-Za-z0-9_\-]{20}\b` |
| `SEC-CONT-ANTHROPIC` | `\bsk-ant-[A-Za-z0-9_\-]{24,}\b` |
| `SEC-CONT-OPENAI` | `\bsk-(?!ant-)(?:proj-)?[A-Za-z0-9_\-]{32,}\b` |
| `SEC-CONT-SLACK` | `\bxox[baprse]-[A-Za-z0-9\-]{10,}\b` |
| `SEC-CONT-GOOGLE` | `\bAIza[0-9A-Za-z_\-]{35}\b` |
| `SEC-CONT-STRIPE` | `\b[rs]k_(?:live\|test)_[A-Za-z0-9]{24,}\b` |
| `SEC-CONT-NPM` | `\bnpm_[A-Za-z0-9]{36}\b` |
| `SEC-CONT-PYPI` | `\bpypi-AgEIcHlwaS5vcmc[A-Za-z0-9_\-]{50,}\b` |
| `SEC-CONT-TELEGRAM` | `\b\d{8,10}:AA[A-Za-z0-9_\-]{33}\b` |
| `SEC-CONT-SENDGRID` | `\bSG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}\b` |
| `SEC-CONT-PEM` | `-----BEGIN (?:RSA \|EC \|DSA \|OPENSSH \|PGP )?PRIVATE KEY-----` |
| `SEC-CONT-PUTTY` | `PuTTY-User-Key-File-\d` |
| `SEC-CONT-JWT` | `\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b` |
| `SEC-CONT-DOCKERAUTH` | `\"auths\"\s*:\s*\{` |
| `SEC-CONT-CONNSTR` | `(?i)\b(?:postgres(?:ql)?\|mysql\|mongodb(?:\+srv)?\|redis\|amqp\|mssql)://[^\s:@/\"']+:[^\s:@/\"']+@` |
| `SEC-CONT-ASSIGN` | `(?i)\b(?:api[_\-]?key\|secret[_\-]?key\|access[_\-]?token\|auth[_\-]?token\|client[_\-]?secret\|private[_\-]?key\|passwd\|password\|bearer[_\-]?token)\b\s*[:=]\s*[\"'][^\"'\n]{8,}[\"']` |

## Local-infrastructure leaks (public shares)

| Rule | Regex |
|------|-------|
| `LOC-RFC1918` | `\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}\|192\.168\.\d{1,3}\.\d{1,3}\|172\.(?:1[6-9]\|2\d\|3[01])\.\d{1,3}\.\d{1,3})\b` |
| `LOC-CGNAT` | `\b100\.(?:6[4-9]\|[7-9]\d\|1[01]\d\|12[0-7])\.\d{1,3}\.\d{1,3}\b` |
| `LOC-IPV6ULA` | `\bfd[0-9a-f]{2}:(?:[0-9a-f]{0,4}:){1,6}[0-9a-f]{0,4}\b` |
| `LOC-UNC` | `\\\\[A-Za-z0-9][A-Za-z0-9._\-]{1,62}\\` |
| `LOC-WINUSER` | `[A-Za-z]:\\Users\\[^\\\s\"'<>\|]+` |
| `LOC-NIXUSER` | `/(?:home\|Users)/(?!runner\b\|user\b\|ubuntu\b)[A-Za-z0-9._\-]+/` |
| `LOC-INTHOST` | `\b[a-z0-9][a-z0-9\-]{0,62}\.(?:local\|lan\|internal\|intranet\|corp\|home\|arpa)\b` |
| `LOC-MAC` | `\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b` |
| `LOC-SSHCFG` | `(?m)^\s*HostName\s+\S+` |

## Filenames that should never ship (glob)

| Rule | Globs |
|------|-------|
| `SEC-PATH-ENV` | `.env .env.* *.env` |
| `SEC-PATH-PEM` | `*.pem *.key *.p8 *.pkcs8 *.pkcs12` |
| `SEC-PATH-PFX` | `*.pfx *.p12 *.jks *.keystore *.bks` |
| `SEC-PATH-SSH` | `id_rsa id_dsa id_ecdsa id_ed25519 *.ppk authorized_keys known_hosts` |
| `SEC-PATH-NETRC` | `.netrc _netrc .git-credentials .pypirc .npmrc .dockercfg` |
| `SEC-PATH-CLOUD` | `credentials credentials.json client_secret*.json service-account*.json gcloud-*.json *serviceaccount*.json azureauth.json` |
| `SEC-PATH-KUBE` | `kubeconfig *.kubeconfig admin.conf` |
| `SEC-PATH-VAULT` | `*.kdbx *.kdb *.opvault *.agilekeychain .vault-token *.gpg secring.*` |
| `SEC-PATH-TFSTATE` | `*.tfstate *.tfstate.backup *.tfvars` |
| `SEC-PATH-HISTORY` | `.bash_history .zsh_history .psql_history .mysql_history .python_history ConsoleHost_history.txt` |
| `SEC-PATH-DBDUMP` | `*.sql *.dump *.sqlite *.sqlite3 *.db` |

## One ripgrep command that runs them all

```bash
# save patterns.txt (one regex per line), then:
rg -n -f patterns.txt --hidden --glob '!.git'
```

See `patterns.txt` in this folder (30 regexes) for the ripgrep `-f` file.
