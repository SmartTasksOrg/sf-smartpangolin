# Husky (JS/TS repos — native Node port, no Python needed)
`.husky/pre-commit`:
```sh
node ./ports/node/bin/cli.js . --mode public
```
`package.json`:
```json
{ "scripts": { "prepublishOnly": "node ./ports/node/bin/cli.js . --mode public" } }
```
The Node port exits non-zero on a SEC-* finding, failing the hook.
