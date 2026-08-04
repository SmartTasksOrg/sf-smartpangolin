# FAQ

**Does it modify my files?**
No. SmartPangolin never rewrites content. A file is included whole or excluded whole.

**Where does the output go?**
One level above `--root` by default (`<root>/../extracted_source/share_archive/`),
so a produced zip is never swept into the next scan or into `git status`.
Override with `--output-folder` / `--archive-dir`.

**Why was a harmless file excluded?**
Fail-closed. The broad `SEC-CONT-ASSIGN` rule and the `OPS-*` family err toward
exclusion. The hit is in `EXCLUSIONS.json`; clear it with one `allow` entry (in
`.pangolin.json` or `--allow path`). There is no `--allow-all` by design.

**public vs private?**
Both exclude secrets. `public` additionally strips local-infrastructure
disclosure (internal IPs, hostnames, home paths, MACs). Use `public` for any
third party; `private` for self-hosted targets where those details are the point.

**Two runs gave different zip hashes.**
Expected — `zip_sha256` embeds generation time. Compare `content_sha256` for
"did the payload change?", or pin `SOURCE_DATE_EPOCH` for byte-identical zips.

**Does it need a virtualenv or dependencies?**
No runtime dependencies — stdlib only, Python 3.8+. It will re-exec under a nearby
`.venv`/`venv` if present (to match the surrounding pipeline); disable with
`--venv none`.

**Can I use it from Java/Go/Node?**
Consume the artifact today (plain JSON + coreutils `SHA256SUMS`). Port the scanner
against `docs/porting.md` if you need native classification. See `adapters/`.

**Is the matched secret stored anywhere?**
No. Only the rule ID, a byte offset, and a match length are recorded — never the
value. The audit record is safe to share.
