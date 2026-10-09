# Security policy

SmartPangolin 3.0.0 is experimental software. It has had no independent
security review. [README "Status"](README.md#status) says what is tested and
what is not.

## Supported versions

| Version | Security fixes |
|---|---|
| 3.0.x | yes |
| older | no; upgrade |

## Reporting a vulnerability

Report privately through GitHub: open
<https://github.com/SmartTasksOrg/sf-smartpangolin>, go to the **Security** tab and
choose **Report a vulnerability** (GitHub private vulnerability reporting).
Only the maintainers can read the report.

Do not open a public issue, pull request or discussion for a vulnerability,
and do not put a working exploit in one.

If the Security tab shows no "Report a vulnerability" button, private
reporting is switched off. Open a public issue that says only "I have a
security report; please enable private vulnerability reporting", with no
details, and wait for a maintainer.

## What to include

- A minimal fixture tree that reproduces the leak, with a **fake**, format-valid
  token (never a real credential).
- The version (`sf-smartpangolin --version`) and your platform.
- The smallest input that shows the problem, and what you expected.
- Whether you checked other versions or ports.

Remove real secrets, tokens and personal data from what you send.

## Packages that pretend to be SmartPangolin

The only package names the maintainers publish are listed with
`"registered": true` in [names.json](names.json). Official releases are built
by `.github/workflows/release.yml` in `SmartTasksOrg/sf-smartpangolin` and published
with trusted publishing, so each file carries a provenance attestation that
names this repository and that workflow.

A package on any registry that uses this project's name but is not listed
there, or a release file without that provenance, is not ours. Report it
through the private form above, and to the registry (PyPI: "Report project
as malware" on the project page; npm: "Report malware" on the package page;
crates.io: help@crates.io).

## What to expect

- An answer in the private report. No response time is promised; this is a
  small project without a security team on call.
- A confirmed issue is fixed in a new release, announced in `CHANGELOG.md`
  and in a GitHub security advisory, with credit to the reporter unless they
  ask not to be named.
- There is no bug bounty.

## Scope

In scope:
- A file that should match a `SEC-PATH-*`, `SEC-DIR-*`, or `SEC-CONT-*` rule but
  is included in a share.
- A `.secret/` file reaching any share, in any mode.
- A merged shard containing content from an excluded file.
- `--verify` reporting `OK` on a tampered or manifest-mismatched archive.

Out of scope:
- False positives (by design; clear them with `allow`).
- Local-infrastructure disclosure in `--share private` (that mode retains it on
  purpose).
- The demo data under `demo/` and the static pages under `site/` (out of scope).

## What it is designed to do

- Matched secret **values are never written** to any artifact — only rule IDs,
  offsets, and lengths.
- `--share public` excludes both secrets and local-infrastructure disclosure.
- Fail-closed: unreadable / oversized / binary / undecodable content is excluded.

## Detection scope & limitations (be honest with yourself)

SmartPangolin uses deterministic, versioned pattern matching. It reliably catches
**unintentional** leaks — a committed `.env`, a pasted key, a secret in a filename,
a key embedded in an image/font/oversize file, or one split by an invisible
character. Red-team regressions for these live in `tests/test_redteam.py`.

It does **not** claim to defeat deliberate obfuscation in text. By design it will
not flag a secret that has been:

- base64/hex-encoded (`QUtJQ...`),
- split by concatenation (`"AKIA" + "IOSF..."`),
- broken by ordinary whitespace or newlines inside the token, or
- padded with word characters in a text file (`xxAKIA...xx`).

Catching those requires entropy analysis, decoding passes, or AST inspection —
non-deterministic, false-positive-prone techniques outside this tool's contract.
An opt-in entropy detector is the intended future mitigation. Treat SmartPangolin
as a strong last line of defence, not a guarantee against a motivated insider.
