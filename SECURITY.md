# Security policy

## Reporting a vulnerability

If you find a way to make SmartPangolin ship a secret it should have caught — a
bypass of any `SEC-*` rule — treat it as a security issue, not a normal bug.

Please report privately via a GitHub security advisory on the repository rather
than a public issue, so a fix can ship before the bypass is widely known.
Include a minimal fixture tree that reproduces the leak (with a **fake**,
format-valid token — never a real credential).

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

## Our guarantees, restated

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
