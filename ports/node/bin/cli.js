#!/usr/bin/env node
'use strict';
const { scan, POLICY_VERSION } = require('../lib/scanner');
const args = process.argv.slice(2);
let root = '.', mode = 'public', json = false, noGit = false, failOnFindings = true, pii = false;
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === '--mode') mode = args[++i];
  else if (a === '--json') json = true;
  else if (a === '--no-gitignore') noGit = true;
  else if (a === '--pii') pii = true;
  else if (a === '--no-fail') failOnFindings = false;
  else if (!a.startsWith('-')) root = a;
}
const dec = scan(root, { mode, respectGitignore: !noGit, pii });
const findings = Object.entries(dec).filter(([, v]) => v !== 'INCLUDE');
if (json) { console.log(JSON.stringify(dec, null, 2)); }
else {
  console.log(`pangolin-check (policy ${POLICY_VERSION}, mode=${mode})`);
  const incl = Object.values(dec).filter(v => v === 'INCLUDE').length;
  console.log(`  ${incl} file(s) OK to share, ${findings.length} excluded:`);
  const byRule = {};
  for (const [, r] of findings) byRule[r] = (byRule[r] || 0) + 1;
  for (const [r, n] of Object.entries(byRule).sort()) console.log(`    ${r.padEnd(18)} ${n}`);
}
process.exit(failOnFindings && findings.some(([, r]) => r.startsWith('SEC-')) ? 1 : 0);
