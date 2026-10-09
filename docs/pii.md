# PII scanning (opt-in higher scan level)

Secrets are always scanned. **PII scanning is off by default** — it catches
personal data in ordinary prose, which is noisier, so you turn it on when you
want it:

    sf-smartpangolin pack --pii --dry-run          # report docs that contain PII
    # or in .pangolin.json:  { "pii": true }

## What it finds
`PII-EMAIL`, `PII-PHONE`, `PII-SSN` (US), `PII-CC` (card numbers). A file that
contains any of these is withheld from the share (like a secret finding).

## Keeping author attribution intact
Two exclusions stop it from flagging legitimate credits:

- **Author context (on by default).** A match on a line that reads like an author
  tag, maintainer line, copyright, or `@author` is kept. So these survive:

      # @author jane@acme.com
      # Copyright (c) 2026 Jane Doe <jane@acme.com>

  Disable with `{ "pii_skip_author": false }` if you want those flagged too.

- **Allow-list.** Exact values you want to keep, e.g. a public author email:

      { "pii": true, "pii_allow": ["hello@acme.com"] }

Both fold into the auditable `policy_sha256`.

## Redaction (clean instead of withhold)
To scrub a document rather than drop it, use the API:

    from sf_smartpangolin.pii import redact_pii
    clean = redact_pii(open("doc.md").read())   # emails -> [EMAIL], etc.

## Scope
All five implementations support `--pii` — the Node, Go, Java and PHP ports carry
the same PII rules and author-context skip, verified by `ports/conformance/run.sh`
(public, private, and `--pii`). Redaction (`redact_pii`) is Python-only.
