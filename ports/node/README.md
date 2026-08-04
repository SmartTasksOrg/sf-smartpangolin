# pangolin-check (Node / React / CI)

Native Node port. No dependencies. Use it as a pre-publish or CI gate.

## Use
```bash
node bin/cli.js <path> [--mode public|private] [--json] [--no-gitignore]
# exit code is non-zero if any SEC-* finding is present (fails CI)
```

## package.json (React/Node projects)
```json
{ "scripts": { "prepublishOnly": "pangolin-check . --mode public" } }
```

## Programmatic
```js
const { scan } = require('pangolin-check/lib/scanner');
const decisions = scan(process.cwd(), { mode: 'public' }); // { "path": "RULE-ID" | "INCLUDE" }
```

Do not run this in the browser — it is a build/CI tool.
