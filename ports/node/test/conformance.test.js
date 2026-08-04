const { scan } = require('../lib/scanner');
const fs = require('fs');
const ref = JSON.parse(fs.readFileSync('/tmp/ref.json', 'utf8'));
const got = scan('/tmp/conf', { mode: 'public' });
let fails = 0;
const keys = new Set([...Object.keys(ref), ...Object.keys(got)]);
for (const k of [...keys].sort()) {
  if (ref[k] !== got[k]) { console.log(`MISMATCH ${k}: py=${ref[k]} node=${got[k]}`); fails++; }
}
console.log(fails ? `\n${fails} mismatch(es)` : `conformance OK — ${Object.keys(ref).length} files match Python`);
process.exit(fails ? 1 : 0);
