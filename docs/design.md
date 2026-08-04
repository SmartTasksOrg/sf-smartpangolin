# Design

SmartPangolin exists to close a specific, repeatable failure: the moment you decide
to share a codebase with a model or a vendor and reach for the two easy options —
zip the folder, or paste a "here is my whole repo" merged text file — is exactly
the moment a live credential leaves your control. The tool that produced this
package was written after a HuggingFace write token reached a share that way.

The name is the design in one image: a pangolin forages out the smallest hidden
things with precision, then rolls into an armored ball of overlapping scales that
nothing penetrates. This tool forages a repo for tiny secrets, then seals what
remains inside a hashed, verifiable shell. Five commitments follow from that, and
everything else is downstream of them.

## 1. Secrets are always excluded — in both modes

A credential is a credential wherever it is going. There is no share mode in
which a `.env`, a `*.pem`, or an inline `hf_…` token ships. What the
`public` / `private` switch controls is *local-infrastructure disclosure*
(internal IPs, hostnames, home paths, MACs) — never secrets.

- **public** — for any third-party endpoint. Secrets *and* local infrastructure
  are stripped.
- **private** — for self-hosted, operator-controlled targets where the internal
  IPs and absolute paths are the whole point. Secrets are still stripped.

## 2. Fail closed

If a file cannot be *proven* safe, it is excluded. Unreadable, oversized (over
8 MB, unscanned), binary (a NUL byte in the first 8 KiB), or undecodable content
does not get shipped on the assumption that it is probably fine. A false positive
is a visible line in `EXCLUSIONS.json` and one `allow` entry to clear. A false
negative is a leaked secret. The asymmetry is the whole design.

## 3. No redaction

A file is included whole or excluded whole. SmartPangolin never rewrites file
contents to "clean" them, for two reasons: partial redaction is the single most
common way a secret survives a scrubber (the second occurrence, the base64 copy,
the one in a comment), and a rewritten file makes the artifact you ship differ
from the tree you tested. Whole-file decisions keep the artifact honest.

## 4. Deterministic — at two levels

- **`content_sha256`** is a hash over the sorted `(path, filehash)` list. It
  depends *only on what was packaged*, not on when. Two runs over an unchanged
  tree always produce the same `content_sha256`. This is the number you compare
  to answer **"did the payload change?"**
- **`zip_sha256`** is a hash of the artifact bytes. It normally differs per run
  because the manifest records generation time. Pin `SOURCE_DATE_EPOCH` and it
  becomes byte-identical across runs — the number for **"is this the exact file
  I produced?"**

Determinism is enforced mechanically: every zip entry gets a fixed DOS timestamp
(1980-01-01), entries are added in sorted order, and compression settings are
fixed.

## 5. Auditable

Every exclusion is recorded with its rule ID, a byte offset, and a match length —
**never the matched value**. The matched secret is not written anywhere, so the
audit record itself is safe to share. Every share and every retention purge is
appended to `share_history.jsonl`. Every operator override names the file and the
rule it overrode. Editing any rule changes `policy_sha256`, which is stamped into
every manifest and ledger entry, so a share can always be traced to the exact
policy that produced it.

## The ordering bug this design fixes

The original stage-2 script merged file *contents* into shards **before** any
secret check. A `.env` therefore ended up inlined verbatim inside
`source_code_part1.txt` — sharing that one text file leaked the token just as
surely as sharing the folder did. SmartPangolin merges **after** classification, from
the included set only. An excluded file is absent from the shards rather than
taking the whole shard down with it. This is verified in the test suite: with a
`.env` present, the merged output contains neither the token pattern nor a
`### .env` header.

## Artifact layout, and why it lives outside the tree

Generated artifacts are written one level *above* `--root` by default
(`<root>/../extracted_source/share_archive/`). That means a produced zip is never
a candidate for the next scan, never shows up in `git status`, and can never be
packaged inside a later share of itself. An absolute `--output-folder` or
`--archive-dir` overrides this.
