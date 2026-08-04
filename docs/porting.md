# Porting SmartPangolin to another language

The Python package is the reference implementation. This page is the contract a
port must satisfy to be **conformant**: given the same tree and policy, it must
produce the same `content_sha256` and the same set of exclusion rule IDs.

You almost never need a full port to *use* SmartPangolin in another stack — the
artifact is plain JSON plus a coreutils-compatible `SHA256SUMS`, so any language
can consume and verify a share today (see the `adapters/` READMEs). Port the
scanner only when you need native, in-build classification without shelling out
to Python.

## Step 1 — get the policy

```bash
pango policy > policy.json
```

This is a versioned document (`smartpangolin.share_policy/v1`) carrying every rule ID,
every glob, every content/local regex description, the allowlist, and the
`policy_sha256`. Pin to a `policy_version`; treat a change in `policy_sha256` as a
breaking change to your port.

## Step 2 — classify a file (order matters)

For each candidate file, in this order, first match wins:

1. **Path allowlist** — if the lower-cased basename is in `path_allowlist`,
   include it, stop.
2. **User deny globs** (`SEC-PATH-USER`) then **`SEC-PATH-*`** — glob-match the
   lower-cased basename. On a hit, exclude with that rule ID.
3. **Backup name** (`OPS-BACKUP`) — basename contains `.bak`, ends `~`, or starts
   `~$`.
4. **Stat** — if you cannot stat it, `OPS-STAT`.
5. **Content scan** (see step 3).

Directories are pruned during the walk by `SEC-DIR-*` / build rules and the
`venv_* / *_venv / *-venv` wildcard.

## Step 3 — content scan (fail-closed)

Given file bytes and size:

- `size > 8 MiB` → if extension in `BINARY_SAFE_EXTS`, allow; else `OPS-OVERSIZE`.
- NUL byte in the **first 8192 bytes** → if in `BINARY_SAFE_EXTS`, allow; else
  `OPS-BINARY`.
- Decode UTF-8, fall back to Latin-1; if both fail, `OPS-UNDECODABLE`.
- Run every `content_rules` regex (secrets, both modes). In **public** mode also
  run every `local_rules` regex.
- If any hit, attribute to the **earliest offset**, breaking ties by rule order
  (rules are listed most-specific-first — this is why Anthropic precedes OpenAI).

Use an RE2-class engine where possible (Go `regexp`, RE2). JS/`java.util.regex`
work too; validate against the fixtures in `tests/`.

## Step 4 — reproduce `content_sha256` exactly

This is the conformance anchor. Sort the *included* files by POSIX path, then:

```
h = SHA256()
for each included file, in sorted path order:
    h.update( utf8(path) )
    h.update( 0x00 )
    h.update( ascii(lowercase_hex_sha256_of_file_bytes) )
    h.update( 0x0A )        # '\n'
content_sha256 = h.hexdigest()
```

Per-file `sha256` is the SHA-256 of the raw file bytes, lower-case hex. Get this
byte-for-byte right and your port and the Python tool agree on payload identity.

## Step 5 — emit the artifacts

Match the schemas in `src/pango/data/manifest.schema.json` and the
`smartpangolin.share_exclusions/v1` / `smartpangolin.share_policy/v1` shapes. For
byte-reproducible zips, use a fixed entry timestamp (1980-01-01), sorted entry
order, and honour `SOURCE_DATE_EPOCH` for the manifest's `generated_utc`.

## Conformance test

Point both implementations at `tests/` fixtures (or any shared tree) and assert:

- identical `content_sha256`,
- identical `by_rule` exclusion tally,
- `verify` passes on each other's zips.

If all three hold, the port is conformant. PRs adding `adapters/<lang>` ports are
welcome.
