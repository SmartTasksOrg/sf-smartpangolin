# SmartPangolin — Node / React

For a **React** app the relevant integration is usually a pre-publish or CI check,
not in-browser scanning (never ship a secret scanner to the client). Wire the
Python tool into your `package.json`:

```json
{
  "scripts": {
    "seal": "pango pack --root . --share public",
    "prepublishOnly": "pango pack --root . --share public --dry-run --debug"
  }
}
```

## Consume an artifact in Node (works today)

```js
import { readFileSync } from "node:fs";
import AdmZip from "adm-zip";

const zip = new AdmZip("share.zip");
const manifest = JSON.parse(zip.readAsText("_SHARE/MANIFEST.json"));
console.log(manifest.share_mode, manifest.file_count, manifest.content_sha256.slice(0, 16));
```

## Port the scanner (roadmap)

JS regex lacks RE2 guarantees; keep the anchored patterns from
`pango policy` and test them against the fixtures in `tests/`. The hashing
recipe (`content_sha256`) is in [../../docs/porting.md](../../docs/porting.md).

> **Update:** a real, conformance-tested native port now lives in `ports/node/`.
